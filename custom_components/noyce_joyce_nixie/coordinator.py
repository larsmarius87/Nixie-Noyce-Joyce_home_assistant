"""Data coordinator for Noyce Joyce Nixie."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import NightModeSettings, NixieBLE, NixieConnectionError, NixieState
from .const import (
    CONF_AUTO_SYNC_ENABLED,
    CONF_AUTO_SYNC_TIME,
    CONF_AUTO_SYNC_INTERVAL_HOURS,
    CONF_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
    CONF_DAYTIME_ENABLED,
    CONF_DAYTIME_OFF_TIME,
    CONF_DAYTIME_ON_TIME,
    CONF_LAST_SYNC_AT,
    CONF_LAST_AUTO_SYNC_AT,
    CONF_SCHEDULE_MODE,
    CONF_SIMPLE_NIGHT_END_TIME,
    CONF_SIMPLE_NIGHT_MODE_ENABLED,
    CONF_SIMPLE_NIGHT_START_TIME,
    CONF_WEEKDAY_OFF_TIME,
    CONF_WEEKDAY_ON_TIME,
    CONF_WEEKEND_OFF_TIME,
    CONF_WEEKEND_ON_TIME,
    DATE_TIME_UUID,
    DEFAULT_AUTO_SYNC_ENABLED,
    DEFAULT_AUTO_SYNC_TIME,
    DEFAULT_AUTO_SYNC_INTERVAL_HOURS,
    DEFAULT_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
    DEFAULT_DAYTIME_ENABLED,
    DEFAULT_DAYTIME_OFF_TIME,
    DEFAULT_DAYTIME_ON_TIME,
    HOURGLASS_UUID,
    MAX_AUTO_SYNC_INTERVAL_HOURS,
    MAX_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
    MIN_AUTO_SYNC_INTERVAL_HOURS,
    MIN_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
    NIGHT_MODE_END_UUID,
    NIGHT_MODE_START_UUID,
    NIGHT_MODE_UUID,
    NIXIE_DOTS_UUID,
    SCHEDULE_END_GRACE,
    SCHEDULE_MODE_SIMPLE,
    SCHEDULE_MODE_WEEKDAY_WEEKEND,
    SCHEDULE_RETRY_DELAY,
    SYNC_RETRY_DELAY,
    TIME_FORMAT_UUID,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScheduleWindow:
    """One interval during which the clock display should be off."""

    start: datetime
    end: datetime
    label: str


class NixieCoordinator(DataUpdateCoordinator[NixieState]):
    """Coordinate BLE reads, writes, clock sync and advanced scheduling."""

    def __init__(self, hass, api: NixieBLE, entry: ConfigEntry) -> None:
        raw_interval = entry.options.get(
            CONF_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
            DEFAULT_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
        )
        try:
            interval_minutes = int(round(float(raw_interval)))
        except (TypeError, ValueError):
            interval_minutes = DEFAULT_BLUETOOTH_UPDATE_INTERVAL_MINUTES
        interval_minutes = max(
            MIN_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
            min(MAX_BLUETOOTH_UPDATE_INTERVAL_MINUTES, interval_minutes),
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=api.name,
            update_interval=timedelta(minutes=interval_minutes),
        )
        self.api = api
        self.entry = entry
        self._unsub_auto_sync = None
        self._unsub_sync_retry = None
        self._unsub_schedule = None
        self._unsub_schedule_retry = None
        self._last_contact: datetime | None = None
        self._schedule_status = "Enkel modus"
        self._schedule_target_window: ScheduleWindow | None = None
        self._programmed_schedule_window: ScheduleWindow | None = None
        self._schedule_last_verified: datetime | None = None
        self._schedule_last_error: str | None = None
        self._started = False
        self._initial_state_loaded = False

        # Entity platforms are loaded before the first BLE connection in v0.6.7.
        # Seed safe fallback data so entities can be created while the coordinator
        # correctly reports them unavailable until a real clock read succeeds.
        self.data = self._fallback_state()
        self.last_update_success = False

    def _fallback_state(self) -> NixieState:
        """Build placeholder state from persisted options where possible."""

        def stored_seconds(*keys: str) -> int:
            for key in keys:
                raw = self.entry.options.get(key)
                if raw is None:
                    continue
                try:
                    value = time.fromisoformat(str(raw)).replace(tzinfo=None)
                except ValueError:
                    continue
                return value.hour * 3600 + value.minute * 60 + value.second
            return 0

        return NixieState(
            firmware_version=None,
            hourglass=4,
            time_format=0,
            nixie_dots=False,
            night_mode=bool(
                self.entry.options.get(CONF_SIMPLE_NIGHT_MODE_ENABLED, False)
            ),
            night_mode_start=stored_seconds(
                CONF_SIMPLE_NIGHT_START_TIME, CONF_WEEKDAY_OFF_TIME
            ),
            night_mode_end=stored_seconds(
                CONF_SIMPLE_NIGHT_END_TIME, CONF_WEEKDAY_ON_TIME
            ),
            clock_time=None,
            clock_drift_seconds=None,
            clock_read_at=None,
        )

    async def _async_update_data(self) -> NixieState:
        try:
            state = await self.api.async_read_state()
            self._record_contact()
            return state
        except NixieConnectionError as err:
            # A proxy may briefly have a stale/busy connection slot after HA
            # startup. Keep the integration loaded and retry quickly instead of
            # leaving the config entry stuck in SETUP_RETRY.
            raise UpdateFailed(str(err), retry_after=30.0) from err

    @callback
    def _async_refresh_finished(self) -> None:
        """Start BLE-dependent scheduling after the first successful clock read."""
        if (
            not self._started
            or not self.last_update_success
            or self._initial_state_loaded
        ):
            return

        self._initial_state_loaded = True
        self._schedule_advanced_programming()

    # ---------------------------------------------------------------------
    # Persistent local options
    # ---------------------------------------------------------------------

    def _option_time(self, key: str, default: str | time) -> time:
        raw_value = self.entry.options.get(key, default)
        if isinstance(raw_value, time):
            return raw_value.replace(tzinfo=None)
        try:
            return time.fromisoformat(str(raw_value)).replace(tzinfo=None)
        except ValueError:
            fallback = default if isinstance(default, time) else time.fromisoformat(default)
            return fallback.replace(tzinfo=None)

    async def _async_set_option(self, key: str, value) -> None:
        options = dict(self.entry.options)
        options[key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_update_listeners()

    @property
    def bluetooth_update_interval_minutes(self) -> int:
        raw = self.entry.options.get(
            CONF_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
            DEFAULT_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
        )
        try:
            value = int(round(float(raw)))
        except (TypeError, ValueError):
            value = DEFAULT_BLUETOOTH_UPDATE_INTERVAL_MINUTES
        return max(
            MIN_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
            min(MAX_BLUETOOTH_UPDATE_INTERVAL_MINUTES, value),
        )

    @property
    def auto_sync_enabled(self) -> bool:
        return bool(self.entry.options.get(CONF_AUTO_SYNC_ENABLED, DEFAULT_AUTO_SYNC_ENABLED))

    @property
    def auto_sync_time(self) -> time:
        return self._option_time(CONF_AUTO_SYNC_TIME, DEFAULT_AUTO_SYNC_TIME)

    @property
    def auto_sync_interval_hours(self) -> int:
        raw = self.entry.options.get(
            CONF_AUTO_SYNC_INTERVAL_HOURS, DEFAULT_AUTO_SYNC_INTERVAL_HOURS
        )
        try:
            value = int(round(float(raw)))
        except (TypeError, ValueError):
            value = DEFAULT_AUTO_SYNC_INTERVAL_HOURS
        return max(
            MIN_AUTO_SYNC_INTERVAL_HOURS,
            min(MAX_AUTO_SYNC_INTERVAL_HOURS, value),
        )

    @property
    def last_auto_sync_at(self) -> datetime | None:
        raw = self.entry.options.get(CONF_LAST_AUTO_SYNC_AT)
        if not raw:
            return None
        try:
            value = datetime.fromisoformat(str(raw))
        except ValueError:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_util.UTC)
        return value.astimezone(dt_util.UTC)

    @property
    def last_sync_at(self) -> datetime | None:
        raw = self.entry.options.get(CONF_LAST_SYNC_AT)
        if not raw:
            return None
        try:
            value = datetime.fromisoformat(str(raw))
        except ValueError:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        return value

    @property
    def last_contact(self) -> datetime | None:
        return self._last_contact

    @property
    def schedule_status(self) -> str:
        return self._schedule_status

    @property
    def schedule_target_window(self) -> ScheduleWindow | None:
        return self._schedule_target_window

    @property
    def programmed_schedule_window(self) -> ScheduleWindow | None:
        return self._programmed_schedule_window

    @property
    def schedule_last_verified(self) -> datetime | None:
        return self._schedule_last_verified

    @property
    def schedule_last_error(self) -> str | None:
        return self._schedule_last_error

    @property
    def schedule_mode(self) -> str:
        value = str(self.entry.options.get(CONF_SCHEDULE_MODE, SCHEDULE_MODE_SIMPLE))
        if value not in (SCHEDULE_MODE_SIMPLE, SCHEDULE_MODE_WEEKDAY_WEEKEND):
            return SCHEDULE_MODE_SIMPLE
        return value

    @property
    def advanced_schedule_enabled(self) -> bool:
        return self.schedule_mode == SCHEDULE_MODE_WEEKDAY_WEEKEND

    def _current_night_start_time(self) -> time:
        return _seconds_to_time(self.data.night_mode_start)

    def _current_night_end_time(self) -> time:
        return _seconds_to_time(self.data.night_mode_end)

    @property
    def weekday_off_time(self) -> time:
        return self._option_time(CONF_WEEKDAY_OFF_TIME, self._current_night_start_time())

    @property
    def weekday_on_time(self) -> time:
        return self._option_time(CONF_WEEKDAY_ON_TIME, self._current_night_end_time())

    @property
    def weekend_off_time(self) -> time:
        return self._option_time(CONF_WEEKEND_OFF_TIME, self._current_night_start_time())

    @property
    def weekend_on_time(self) -> time:
        return self._option_time(CONF_WEEKEND_ON_TIME, self._current_night_end_time())

    @property
    def daytime_enabled(self) -> bool:
        return bool(self.entry.options.get(CONF_DAYTIME_ENABLED, DEFAULT_DAYTIME_ENABLED))

    @property
    def daytime_off_time(self) -> time:
        return self._option_time(CONF_DAYTIME_OFF_TIME, DEFAULT_DAYTIME_OFF_TIME)

    @property
    def daytime_on_time(self) -> time:
        return self._option_time(CONF_DAYTIME_ON_TIME, DEFAULT_DAYTIME_ON_TIME)

    @staticmethod
    def _night_mode_matches(
        settings: NightModeSettings, enabled: bool, start_seconds: int, end_seconds: int
    ) -> bool:
        return (
            settings.enabled == enabled
            and settings.start_seconds == start_seconds % 86400
            and settings.end_seconds == end_seconds % 86400
        )

    @callback
    def _apply_night_mode_readback(self, settings: NightModeSettings) -> None:
        """Mirror verified/read-back scheduler values into coordinator data."""
        self.async_set_updated_data(
            replace(
                self.data,
                night_mode=settings.enabled,
                night_mode_start=settings.start_seconds,
                night_mode_end=settings.end_seconds,
            )
        )

    @callback
    def _set_schedule_checking(self, window: ScheduleWindow) -> None:
        self._schedule_target_window = window
        self._schedule_status = "Kontrollerer"
        self._schedule_last_error = None
        self.async_update_listeners()

    @callback
    def _set_schedule_verified(self, window: ScheduleWindow) -> None:
        self._schedule_target_window = window
        self._programmed_schedule_window = window
        self._schedule_status = "Bekreftet"
        self._schedule_last_verified = dt_util.utcnow()
        self._schedule_last_error = None
        self.async_update_listeners()

    @callback
    def _set_schedule_failed(self, window: ScheduleWindow, error: str) -> None:
        self._schedule_target_window = window
        self._schedule_status = "Ikke bekreftet – prøver igjen"
        self._schedule_last_error = error
        self.async_update_listeners()

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------

    @callback
    def async_start(self) -> None:
        """Start timers owned by the integration."""
        self._started = True
        self._schedule_auto_sync()
        if self.advanced_schedule_enabled:
            self._schedule_status = "Venter på klokka"
            self.async_update_listeners()
        # Advanced schedule programming is deferred until the first successful
        # BLE read. This avoids competing startup connections through a proxy.

    @callback
    def async_shutdown(self) -> None:
        """Cancel all timers owned by the integration."""
        self._started = False
        for attr in (
            "_unsub_auto_sync",
            "_unsub_sync_retry",
            "_unsub_schedule",
            "_unsub_schedule_retry",
        ):
            unsub = getattr(self, attr)
            if unsub is not None:
                unsub()
                setattr(self, attr, None)

    @callback
    def _record_contact(self) -> None:
        self._last_contact = dt_util.utcnow()
        self.async_update_listeners()

    # ---------------------------------------------------------------------
    # Automatic time synchronization with retry
    # ---------------------------------------------------------------------

    @callback
    def _schedule_auto_sync(self) -> None:
        if self._unsub_auto_sync is not None:
            self._unsub_auto_sync()
            self._unsub_auto_sync = None

        if not self.auto_sync_enabled:
            if self._unsub_sync_retry is not None:
                self._unsub_sync_retry()
                self._unsub_sync_retry = None
            return

        now = dt_util.now()
        interval = timedelta(hours=self.auto_sync_interval_hours)
        last_auto_sync = self.last_auto_sync_at

        if last_auto_sync is None:
            # Before the first successful automatic synchronization, use the
            # configured time-of-day as the anchor.
            next_run = datetime.combine(
                now.date(), self.auto_sync_time, tzinfo=now.tzinfo
            )
            if next_run <= now:
                next_run = datetime.combine(
                    now.date() + timedelta(days=1),
                    self.auto_sync_time,
                    tzinfo=now.tzinfo,
                )
        else:
            # Once automatic synchronization has succeeded, preserve a true
            # interval independent of manual syncs. Calculate in UTC to avoid
            # DST transitions stretching or shortening the selected interval.
            now_utc = dt_util.utcnow()
            next_run_utc = last_auto_sync + interval
            while next_run_utc <= now_utc:
                next_run_utc += interval
            next_run = dt_util.as_local(next_run_utc)

        _LOGGER.debug(
            "Next Nixie automatic clock sync scheduled for %s (interval %sh)",
            next_run,
            self.auto_sync_interval_hours,
        )
        self._unsub_auto_sync = async_track_point_in_time(
            self.hass, self._handle_auto_sync, next_run
        )

    @callback
    def _handle_auto_sync(self, _now: datetime) -> None:
        self._unsub_auto_sync = None
        self.hass.async_create_task(self._async_auto_sync_and_reschedule())

    async def _async_auto_sync_and_reschedule(self) -> None:
        try:
            await self.async_sync_clock(auto=True)
            _LOGGER.debug("Automatic Nixie clock synchronization completed")
        except NixieConnectionError:
            _LOGGER.warning(
                "Automatic Nixie clock synchronization failed; retrying in %s minutes",
                int(SYNC_RETRY_DELAY.total_seconds() // 60),
            )
            self._schedule_sync_retry()
        finally:
            self._schedule_auto_sync()

    @callback
    def _schedule_sync_retry(self) -> None:
        if not self.auto_sync_enabled or self._unsub_sync_retry is not None:
            return
        self._unsub_sync_retry = async_call_later(
            self.hass, SYNC_RETRY_DELAY.total_seconds(), self._handle_sync_retry
        )

    @callback
    def _handle_sync_retry(self, _now) -> None:
        self._unsub_sync_retry = None
        self.hass.async_create_task(self._async_retry_sync())

    async def _async_retry_sync(self) -> None:
        if not self.auto_sync_enabled:
            return
        try:
            await self.async_sync_clock(auto=True)
            _LOGGER.info("Nixie clock synchronization retry succeeded")
        except NixieConnectionError:
            _LOGGER.debug("Nixie clock synchronization retry failed")
            self._schedule_sync_retry()

    async def async_set_bluetooth_update_interval_minutes(self, value: int) -> None:
        interval = max(
            MIN_BLUETOOTH_UPDATE_INTERVAL_MINUTES,
            min(MAX_BLUETOOTH_UPDATE_INTERVAL_MINUTES, int(round(value))),
        )
        await self._async_set_option(CONF_BLUETOOTH_UPDATE_INTERVAL_MINUTES, interval)

        # DataUpdateCoordinator supports changing update_interval at runtime.
        # Reschedule immediately so the new interval applies from now, without
        # requiring a Home Assistant or integration restart.
        self.update_interval = timedelta(minutes=interval)
        self._schedule_refresh()

    async def async_set_auto_sync_enabled(self, enabled: bool) -> None:
        await self._async_set_option(CONF_AUTO_SYNC_ENABLED, bool(enabled))
        self._schedule_auto_sync()

    async def async_set_auto_sync_time(self, value: time) -> None:
        clean_value = value.replace(tzinfo=None)
        options = dict(self.entry.options)
        options[CONF_AUTO_SYNC_TIME] = clean_value.isoformat()
        # Changing the anchor time intentionally resets the automatic cadence.
        options.pop(CONF_LAST_AUTO_SYNC_AT, None)
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_update_listeners()
        self._schedule_auto_sync()

    async def async_set_auto_sync_interval_hours(self, value: int) -> None:
        interval = max(
            MIN_AUTO_SYNC_INTERVAL_HOURS,
            min(MAX_AUTO_SYNC_INTERVAL_HOURS, int(round(value))),
        )
        await self._async_set_option(CONF_AUTO_SYNC_INTERVAL_HOURS, interval)
        self._schedule_auto_sync()

    # ---------------------------------------------------------------------
    # Advanced display scheduler
    # ---------------------------------------------------------------------

    def _night_window_for_wake_date(self, wake_date: date) -> ScheduleWindow:
        """Build a night window.

        Weekday/weekend is selected from the morning/display-on date. This makes
        Friday night use the weekend schedule for Saturday morning, and Sunday
        night use the weekday schedule for Monday morning.
        """
        weekend = wake_date.weekday() >= 5
        off_time = self.weekend_off_time if weekend else self.weekday_off_time
        on_time = self.weekend_on_time if weekend else self.weekday_on_time
        tz = dt_util.now().tzinfo

        end = datetime.combine(wake_date, on_time, tzinfo=tz)
        if off_time >= on_time:
            start_date = wake_date - timedelta(days=1)
        else:
            start_date = wake_date
        start = datetime.combine(start_date, off_time, tzinfo=tz)
        return ScheduleWindow(start, end, "Natt")

    def _daytime_window_for_date(self, day: date) -> ScheduleWindow | None:
        if not self.daytime_enabled or day.weekday() >= 5:
            return None
        tz = dt_util.now().tzinfo
        start = datetime.combine(day, self.daytime_off_time, tzinfo=tz)
        end_day = day if self.daytime_on_time > self.daytime_off_time else day + timedelta(days=1)
        end = datetime.combine(end_day, self.daytime_on_time, tzinfo=tz)
        return ScheduleWindow(start, end, "Dagtid")

    def _schedule_windows(self, now: datetime | None = None) -> list[ScheduleWindow]:
        now = now or dt_util.now()
        windows: list[ScheduleWindow] = []
        # Include enough past/future dates to cover a cross-midnight active window
        # and determine several upcoming events.
        for offset in range(-1, 9):
            day = now.date() + timedelta(days=offset)
            windows.append(self._night_window_for_wake_date(day))
            daytime = self._daytime_window_for_date(day)
            if daytime is not None:
                windows.append(daytime)
        # De-duplicate and sort.
        unique = {(w.start, w.end, w.label): w for w in windows}
        return sorted(unique.values(), key=lambda w: (w.start, w.end, w.label))

    def active_or_next_window(self, now: datetime | None = None) -> ScheduleWindow | None:
        if not self.advanced_schedule_enabled:
            return None
        now = now or dt_util.now()
        windows = self._schedule_windows(now)
        active = [w for w in windows if w.start <= now < w.end]
        if active:
            return min(active, key=lambda w: w.end)
        upcoming = [w for w in windows if w.start > now]
        return min(upcoming, key=lambda w: w.start) if upcoming else None

    def next_schedule_event(self, now: datetime | None = None) -> tuple[datetime, str] | None:
        """Return the next actual display ON/OFF event."""
        now = now or dt_util.now()
        events: list[tuple[datetime, str]] = []

        if self.advanced_schedule_enabled:
            for window in self._schedule_windows(now):
                if window.start > now:
                    events.append((window.start, "Display av"))
                if window.end > now:
                    events.append((window.end, "Display på"))
        elif self.data.night_mode:
            # In simple mode, use the clock's own single daily interval.
            start_t = _seconds_to_time(self.data.night_mode_start)
            end_t = _seconds_to_time(self.data.night_mode_end)
            tz = now.tzinfo
            for offset in range(0, 3):
                day = now.date() + timedelta(days=offset)
                start_dt = datetime.combine(day, start_t, tzinfo=tz)
                end_day = day + timedelta(days=1) if start_t >= end_t else day
                end_dt = datetime.combine(end_day, end_t, tzinfo=tz)
                if start_dt > now:
                    events.append((start_dt, "Display av"))
                if end_dt > now:
                    events.append((end_dt, "Display på"))

        return min(events, key=lambda item: item[0]) if events else None

    @callback
    def _schedule_advanced_programming(self) -> None:
        if self._unsub_schedule is not None:
            self._unsub_schedule()
            self._unsub_schedule = None
        if self._unsub_schedule_retry is not None:
            self._unsub_schedule_retry()
            self._unsub_schedule_retry = None

        if not self._initial_state_loaded:
            self._schedule_status = "Venter på klokka"
            self._schedule_target_window = None
            self._programmed_schedule_window = None
            self._schedule_last_error = None
            self.async_update_listeners()
            return

        if not self.advanced_schedule_enabled:
            self._schedule_status = "Enkel modus"
            self._schedule_target_window = None
            self._programmed_schedule_window = None
            self._schedule_last_error = None
            self.async_update_listeners()
            return

        self.hass.async_create_task(self._async_program_active_or_next_window())

    async def _async_program_active_or_next_window(self) -> None:
        """Ensure the clock stores the desired interval and verify by read-back.

        The scheduler is event-driven: it first reads the values already stored in
        the clock. A write is only made when those values differ from the desired
        interval. Failed connections or mismatched read-back values are retried.
        """
        if not self.advanced_schedule_enabled:
            return

        window = self.active_or_next_window()
        if window is None:
            return

        start_seconds = _time_to_seconds(window.start.timetz().replace(tzinfo=None))
        end_seconds = _time_to_seconds(window.end.timetz().replace(tzinfo=None))
        self._set_schedule_checking(window)

        try:
            # First read what the clock already has. This prevents needless writes
            # after HA restarts or when the correct interval is already programmed.
            current = await self.api.async_read_night_mode_settings()
            self._record_contact()
            self._apply_night_mode_readback(current)

            if self._night_mode_matches(current, True, start_seconds, end_seconds):
                _LOGGER.debug(
                    "Nixie %s window already programmed and verified: %s -> %s",
                    window.label,
                    window.start,
                    window.end,
                )
                self._set_schedule_verified(window)
                self._schedule_after_window(window)
                return

            # Values differ: write once, wait for the GATT write responses, then
            # read the three characteristics back in the same BLE connection.
            confirmed = await self.api.async_program_night_mode_verified(
                True, start_seconds, end_seconds
            )
            self._record_contact()
            self._apply_night_mode_readback(confirmed)

            if not self._night_mode_matches(confirmed, True, start_seconds, end_seconds):
                error = (
                    "Read-back stemmer ikke: forventet "
                    f"på/{start_seconds}/{end_seconds}, fikk "
                    f"{'på' if confirmed.enabled else 'av'}/"
                    f"{confirmed.start_seconds}/{confirmed.end_seconds}"
                )
                _LOGGER.warning(
                    "Nixie schedule write was acknowledged but verification failed: %s",
                    error,
                )
                self._set_schedule_failed(window, error)
                self._schedule_schedule_retry()
                return

            _LOGGER.debug(
                "Programmed and verified Nixie %s window: %s -> %s",
                window.label,
                window.start,
                window.end,
            )
            self._set_schedule_verified(window)
            self._schedule_after_window(window)
        except NixieConnectionError as err:
            error = str(err)
            self._set_schedule_failed(window, error)
            _LOGGER.warning(
                "Could not verify/program Nixie display schedule; retrying in %s minutes: %s",
                int(SCHEDULE_RETRY_DELAY.total_seconds() // 60),
                error,
            )
            self._schedule_schedule_retry()

    @callback
    def _schedule_after_window(self, window: ScheduleWindow) -> None:
        if self._unsub_schedule_retry is not None:
            self._unsub_schedule_retry()
            self._unsub_schedule_retry = None
        if self._unsub_schedule is not None:
            self._unsub_schedule()
        run_at = window.end + SCHEDULE_END_GRACE
        if run_at <= dt_util.now():
            run_at = dt_util.now() + timedelta(seconds=5)
        self._unsub_schedule = async_track_point_in_time(
            self.hass, self._handle_schedule_boundary, run_at
        )

    @callback
    def _handle_schedule_boundary(self, _now: datetime) -> None:
        self._unsub_schedule = None
        self.hass.async_create_task(self._async_program_active_or_next_window())

    @callback
    def _schedule_schedule_retry(self) -> None:
        if not self.advanced_schedule_enabled or self._unsub_schedule_retry is not None:
            return
        self._unsub_schedule_retry = async_call_later(
            self.hass,
            SCHEDULE_RETRY_DELAY.total_seconds(),
            self._handle_schedule_retry,
        )

    @callback
    def _handle_schedule_retry(self, _now) -> None:
        self._unsub_schedule_retry = None
        self.hass.async_create_task(self._async_program_active_or_next_window())

    async def async_set_schedule_mode(self, mode: str) -> None:
        if mode not in (SCHEDULE_MODE_SIMPLE, SCHEDULE_MODE_WEEKDAY_WEEKEND):
            raise ValueError(f"Unknown schedule mode: {mode}")
        if mode == self.schedule_mode:
            return

        if mode == SCHEDULE_MODE_WEEKDAY_WEEKEND:
            # Preserve the clock's current simple-mode settings so changing back
            # to Enkel restores exactly what the user had before. Also freeze the
            # initial advanced weekday/weekend defaults instead of letting them
            # follow whatever interval the scheduler most recently programmed.
            current_start = _seconds_to_time(self.data.night_mode_start).isoformat()
            current_end = _seconds_to_time(self.data.night_mode_end).isoformat()
            options = dict(self.entry.options)
            options[CONF_SIMPLE_NIGHT_MODE_ENABLED] = bool(self.data.night_mode)
            options[CONF_SIMPLE_NIGHT_START_TIME] = current_start
            options[CONF_SIMPLE_NIGHT_END_TIME] = current_end
            options.setdefault(CONF_WEEKDAY_OFF_TIME, current_start)
            options.setdefault(CONF_WEEKDAY_ON_TIME, current_end)
            options.setdefault(CONF_WEEKEND_OFF_TIME, current_start)
            options.setdefault(CONF_WEEKEND_ON_TIME, current_end)
            options[CONF_SCHEDULE_MODE] = mode
            self.hass.config_entries.async_update_entry(self.entry, options=options)
            self.async_update_listeners()
            self._schedule_advanced_programming()
            return

        # Returning to Enkel restores the native settings that were present
        # immediately before advanced scheduling was enabled. Do the BLE writes
        # first so a connection failure does not leave HA claiming simple mode
        # while the clock still contains an advanced/daytime interval.
        saved_start = self._option_time(
            CONF_SIMPLE_NIGHT_START_TIME, self._current_night_start_time()
        )
        saved_end = self._option_time(
            CONF_SIMPLE_NIGHT_END_TIME, self._current_night_end_time()
        )
        saved_enabled = bool(
            self.entry.options.get(CONF_SIMPLE_NIGHT_MODE_ENABLED, self.data.night_mode)
        )

        start_seconds = _time_to_seconds(saved_start)
        end_seconds = _time_to_seconds(saved_end)
        confirmed = await self.api.async_program_night_mode_verified(
            saved_enabled, start_seconds, end_seconds
        )
        self._record_contact()
        self._apply_night_mode_readback(confirmed)
        if not self._night_mode_matches(
            confirmed, saved_enabled, start_seconds, end_seconds
        ):
            raise NixieConnectionError(
                "Klokka kvitterte på skrivingen, men de gjenleste nattmodusverdiene "
                "stemte ikke med enkel-modusen som skulle gjenopprettes."
            )

        await self._async_set_option(CONF_SCHEDULE_MODE, mode)
        self._schedule_advanced_programming()

    async def _async_set_schedule_time(self, key: str, value: time) -> None:
        await self._async_set_option(key, value.replace(tzinfo=None).isoformat())
        self._schedule_advanced_programming()

    async def async_set_weekday_off_time(self, value: time) -> None:
        await self._async_set_schedule_time(CONF_WEEKDAY_OFF_TIME, value)

    async def async_set_weekday_on_time(self, value: time) -> None:
        await self._async_set_schedule_time(CONF_WEEKDAY_ON_TIME, value)

    async def async_set_weekend_off_time(self, value: time) -> None:
        await self._async_set_schedule_time(CONF_WEEKEND_OFF_TIME, value)

    async def async_set_weekend_on_time(self, value: time) -> None:
        await self._async_set_schedule_time(CONF_WEEKEND_ON_TIME, value)

    async def async_set_daytime_enabled(self, enabled: bool) -> None:
        await self._async_set_option(CONF_DAYTIME_ENABLED, bool(enabled))
        self._schedule_advanced_programming()

    async def async_set_daytime_off_time(self, value: time) -> None:
        await self._async_set_schedule_time(CONF_DAYTIME_OFF_TIME, value)

    async def async_set_daytime_on_time(self, value: time) -> None:
        await self._async_set_schedule_time(CONF_DAYTIME_ON_TIME, value)

    # ---------------------------------------------------------------------
    # Direct clock controls
    # ---------------------------------------------------------------------

    async def async_set_nixie_dots(self, enabled: bool) -> None:
        await self.api.async_write_u8(NIXIE_DOTS_UUID, int(enabled))
        self._record_contact()
        self.async_set_updated_data(replace(self.data, nixie_dots=enabled))

    async def async_set_night_mode(self, enabled: bool) -> None:
        await self.api.async_write_u8(NIGHT_MODE_UUID, int(enabled))
        self._record_contact()
        self.async_set_updated_data(replace(self.data, night_mode=enabled))

    async def async_set_time_format(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Time format must be 0 or 1")
        await self.api.async_write_u8(TIME_FORMAT_UUID, value)
        self._record_contact()
        self.async_set_updated_data(replace(self.data, time_format=value))

    async def async_set_hourglass(self, value: int) -> None:
        if value not in range(5):
            raise ValueError("Hourglass value must be 0..4")
        await self.api.async_write_u8(HOURGLASS_UUID, value)
        self._record_contact()
        self.async_set_updated_data(replace(self.data, hourglass=value))

    async def async_set_night_start(self, seconds: int) -> None:
        seconds %= 86400
        await self.api.async_write_u32(NIGHT_MODE_START_UUID, seconds)
        self._record_contact()
        self.async_set_updated_data(replace(self.data, night_mode_start=seconds))

    async def async_set_night_end(self, seconds: int) -> None:
        seconds %= 86400
        await self.api.async_write_u32(NIGHT_MODE_END_UUID, seconds)
        self._record_contact()
        self.async_set_updated_data(replace(self.data, night_mode_end=seconds))

    async def async_sync_clock(self, *, auto: bool = False) -> None:
        """Synchronize the clock to Home Assistant local wall time."""
        now = dt_util.now()
        offset = now.utcoffset()
        offset_seconds = int(offset.total_seconds()) if offset is not None else 0
        local_epoch = int(now.timestamp()) + offset_seconds
        await self.api.async_write_u32(DATE_TIME_UUID, local_epoch)
        self._record_contact()

        options = dict(self.entry.options)
        synced_at = dt_util.utcnow()
        options[CONF_LAST_SYNC_AT] = synced_at.isoformat()
        if auto:
            options[CONF_LAST_AUTO_SYNC_AT] = synced_at.isoformat()
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_update_listeners()


def _seconds_to_time(seconds: int) -> time:
    seconds %= 86400
    hour, remainder = divmod(seconds, 3600)
    minute, second = divmod(remainder, 60)
    return time(hour=hour, minute=minute, second=second)


def _time_to_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second

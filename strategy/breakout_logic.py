"""
Breakout and confirmation detection logic
(Updated to post-10:00 two-candle confirmation on Nifty 5-minute candles)
"""
from typing import Optional, Literal
from dataclasses import dataclass
from datetime import time
import pandas as pd
from utils.logger import setup_logger

logger = setup_logger('BreakoutDetector', level='INFO')

TradeSide = Literal['CALL', 'PUT', 'NONE']

@dataclass
class BreakoutState:
    """Kept for backward-compatibility (no longer used for entries)."""
    detected: bool = False
    breakout_high: Optional[float] = None
    breakout_candle_close: Optional[float] = None
    confirmation_pending: bool = False

class BreakoutDetector:
    """
    Detect entries using *Nifty 5-minute* two-candle confirmation AFTER 10:00:
      - CALL: candle k close > RN AND candle k+1 close > RN AND > k close
      - PUT : candle k close < GN AND candle k+1 close < GN AND < k close

    Notes:
    - This class preserves the old public API (decide_side, check_breakout, check_confirmation),
      but entries are now decided entirely inside decide_side based on Nifty candles.
    - After an exit or stop-loss, call `notify_position_closed()` to re-arm the detector.
    """

    def __init__(self):
        # old fields (retained so external code doesn't break)
        self.call_breakout = BreakoutState()
        self.put_breakout = BreakoutState()

        self.current_side: TradeSide = 'NONE'

        # NEW: state for the two-candle confirmation logic
        self._prev_nifty5: Optional[pd.Series] = None  # previous completed 5m Nifty candle
        self._armed: bool = False                      # can take a fresh entry?
        self._trading_window_open: bool = False        # true after 10:00 (based on candle ts)
        self._trade_start_time: time = time(10, 0)     # 10:00
        self._call_rearm_pending: bool = False         # require close back below RN before new CALL entry attempt
        self._put_rearm_pending: bool = False          # require close back above GN before new PUT entry attempt

    # -------------------- new helpers --------------------

    def notify_position_closed(self):
        """
        Call this when your position is fully closed (SL/target/manual)
        to re-arm the detector for the next setup.
        """
        if self._trading_window_open:
            if self.current_side == 'CALL':
                # require Nifty to close back below RN before next CALL entry
                self._call_rearm_pending = True
            elif self.current_side == 'PUT':
                # require Nifty to close back above GN before next PUT entry
                self._put_rearm_pending = True
            self._armed = True
            self._prev_nifty5 = None  # force fresh two-candle sequence post-exit
            logger.info(
                "Re-armed after position closed. Rearm pending: CALL=%s, PUT=%s",
                self._call_rearm_pending,
                self._put_rearm_pending,
            )
            # clear current side after recording which flag was set
            self.current_side = 'NONE'

    def _past_start_time(self, dt) -> bool:
        """
        dt: pandas.Timestamp or datetime from the Nifty candle.
        Returns True once local time is >= 10:00.
        """
        # pandas.Timestamp has .time(); naive or tz-aware works for local-market backtests.
        try:
            return dt.time() >= self._trade_start_time
        except Exception:
            # If dt is string or unexpected, be safe: do not allow trading.
            logger.warning("Unexpected timestamp in candle; gating until parsed correctly.")
            return False

    # -------------------- main API (unchanged signature) --------------------

    def decide_side(self, nifty_candle: pd.Series, RN: float, GN: float) -> TradeSide:
        """
        Decide trading side based on *Nifty 5-min candles* with two-candle confirmation.

        Args:
            nifty_candle: pd.Series with keys ['timestamp','open','high','low','close']
            RN: Resistance level
            GN: (mid/green) level

        Returns:
            'CALL' when two-candle bullish confirmation
            'PUT'  when two-candle bearish confirmation
            'NONE' otherwise
        """
        # basic guards
        if nifty_candle is None or 'timestamp' not in nifty_candle or 'close' not in nifty_candle:
            return 'NONE'

        ts = nifty_candle['timestamp']
        close = float(nifty_candle['close'])

        # 1) open trading window after 10:00
        if not self._trading_window_open:
            if self._past_start_time(ts):
                self._trading_window_open = True
                self._armed = True  # arm immediately once window opens
                logger.info("Trading window opened (>= 10:00) and armed.")
            else:
                # before 10:00, just buffer last candle
                self._prev_nifty5 = nifty_candle
                return 'NONE'

        # 2) if not armed (e.g., just took a trade and haven't exited), do nothing
        if not self._armed:
            self._prev_nifty5 = nifty_candle
            return 'NONE'

        # 3) need previous candle for 2-candle confirmation
        if self._prev_nifty5 is None:
            self._prev_nifty5 = nifty_candle
            return 'NONE'

        prev = self._prev_nifty5
        prev_close = float(prev['close'])
        prev_ts = prev.get('timestamp') if isinstance(prev, (pd.Series, dict)) else None
        logger.info(f"Nifty candle: {ts}: {prev_close:.2f} → {close:.2f}")

        # Handle re-arm gating based on post-exit conditions
        if self._call_rearm_pending:
            if prev_close <= RN and close <= RN:
                # price has closed back below RN on both candles since exit
                self._call_rearm_pending = False
                logger.info(
                    "CALL rearm condition satisfied: prev_close=%.2f, close=%.2f <= RN=%.2f",
                    prev_close,
                    close,
                    RN,
                )
            else:
                logger.debug(
                    "CALL rearm pending. Need closes <= RN. prev_close=%.2f, close=%.2f, RN=%.2f",
                    prev_close,
                    close,
                    RN,
                )
                self._prev_nifty5 = nifty_candle
                return 'NONE'

        if self._put_rearm_pending:
            if prev_close >= GN and close >= GN:
                # price has closed back above GN on both candles since exit
                self._put_rearm_pending = False
                logger.info(
                    "PUT rearm condition satisfied: prev_close=%.2f, close=%.2f >= GN=%.2f",
                    prev_close,
                    close,
                    GN,
                )
            else:
                logger.debug(
                    "PUT rearm pending. Need closes >= GN. prev_close=%.2f, close=%.2f, GN=%.2f",
                    prev_close,
                    close,
                    GN,
                )
                self._prev_nifty5 = nifty_candle
                return 'NONE'

        # ---- Two-candle confirmation checks (strict inequalities) ----
        # CALL: prev.close > RN AND curr.close > RN AND curr.close > prev.close
        if (prev_close > RN) and (close > RN) and (close > prev_close):
            self.current_side = 'CALL'
            self._armed = False        # disarm until exit
            self._prev_nifty5 = nifty_candle
            logger.info(
                f"✅ CALL confirmed: prev_close={prev_close:.2f} > RN={RN:.2f}, "
                f"curr_close={close:.2f} > RN and > prev_close"
            )
            return 'CALL'

        # PUT: prev.close < GN AND curr.close < GN AND curr.close < prev.close
        if (prev_close < GN) and (close < GN) and (close < prev_close):
            self.current_side = 'PUT'
            self._armed = False        # disarm until exit
            self._prev_nifty5 = nifty_candle
            logger.info(
                f"✅ PUT confirmed: prev_close={prev_close:.2f} < GN={GN:.2f}, "
                f"curr_close={close:.2f} < GN and < prev_close"
            )
            return 'PUT'

        # 4) no setup; slide the window
        self.current_side = 'NONE'
        self._prev_nifty5 = nifty_candle
        return 'NONE'

    # -------------------- legacy API (kept for compatibility) --------------------

    def check_breakout(
        self,
        option_candle: pd.Series,
        reference_high: float,
        side: TradeSide
    ) -> bool:
        """
        Legacy no-op: entries are now decided solely by decide_side()
        based on Nifty two-candle confirmation after 10:15.
        Kept to avoid breaking existing callers.
        """
        # Keep state reset semantics if someone still calls this
        state = self.call_breakout if side == 'CALL' else self.put_breakout
        state.detected = False
        state.breakout_high = None
        state.breakout_candle_close = None
        state.confirmation_pending = False
        return False

    def check_confirmation(
        self,
        option_candle: pd.Series,
        reference_high: float,
        side: TradeSide
    ) -> bool:
        """
        Legacy no-op: confirmation is part of the two-candle Nifty rule in decide_side().
        """
        # Ensure legacy state is cleared
        state = self.call_breakout if side == 'CALL' else self.put_breakout
        state.detected = False
        state.breakout_high = None
        state.breakout_candle_close = None
        state.confirmation_pending = False
        return False

    def reset_breakout(self, side: TradeSide):
        """Reset breakout state for a side (legacy compatibility)."""
        if side == 'CALL':
            self.call_breakout = BreakoutState()
        elif side == 'PUT':
            self.put_breakout = BreakoutState()
        logger.info(f"Breakout state reset for {side}")

    def reset_all(self):
        """Reset all states and disarm until 10:00 logic opens again."""
        self.call_breakout = BreakoutState()
        self.put_breakout = BreakoutState()
        self.current_side = 'NONE'
        self._prev_nifty5 = None
        self._armed = False
        self._trading_window_open = False
        logger.info("All breakout states reset")

    def get_current_side(self) -> TradeSide:
        """Get last signaled side ('CALL'/'PUT') or 'NONE'."""
        return self.current_side

# Global instance (unchanged)
breakout_detector = BreakoutDetector()

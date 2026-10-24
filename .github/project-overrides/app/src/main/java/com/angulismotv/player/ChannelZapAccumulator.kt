package com.angulismotv.player

/**
 * Accumulates rapid CH+/CH- inputs received while a channel transition is active.
 * The caller drains the net delta after that transition rather than overlapping player reloads.
 */
internal class ChannelZapAccumulator {
    private var queuedDelta = 0

    fun accumulate(delta: Int) {
        queuedDelta += delta
    }

    fun consume(): Int {
        val delta = queuedDelta
        queuedDelta = 0
        return delta
    }

    fun clear() {
        queuedDelta = 0
    }
}

package com.angulismotv.player

import org.junit.Assert.assertEquals
import org.junit.Test

class ChannelZapAccumulatorTest {
    @Test
    fun accumulatesRapidForwardAndBackwardInputs() {
        val queue = ChannelZapAccumulator()
        queue.accumulate(1)
        queue.accumulate(1)
        queue.accumulate(-1)
        assertEquals(1, queue.consume())
        assertEquals(0, queue.consume())
    }

    @Test
    fun oppositeInputsCancelOut() {
        val queue = ChannelZapAccumulator()
        queue.accumulate(1)
        queue.accumulate(-1)
        assertEquals(0, queue.consume())
    }

    @Test
    fun clearingDropsPendingZaps() {
        val queue = ChannelZapAccumulator()
        queue.accumulate(3)
        queue.clear()
        assertEquals(0, queue.consume())
    }
}

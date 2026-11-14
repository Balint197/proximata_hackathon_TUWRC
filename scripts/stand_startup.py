"""Post-RPC admission check for the supervised stand diagnostic."""
def safe_to_enable(state, now, aborted, watchdog_alive):
    return (not aborted and watchdog_alive and
            state['button'] is False and
            0 <= now-state['button_time'] < .15 and
            0 <= now-state['watchdog_time'] < .15 and
            state['watchdog_prepared'] and not state['watchdog_tripped'] and
            state['power'] is True)


def stop_motion_sources(stimulus, gate, trip, kill):
    if stimulus is not None and stimulus.poll() is None:
        try: kill(stimulus)
        except OSError: pass
    success=True
    try: trip()
    except Exception: success=False
    finally:
        if gate is not None and gate.poll() is None:
            try: kill(gate)
            except OSError: pass
    return success

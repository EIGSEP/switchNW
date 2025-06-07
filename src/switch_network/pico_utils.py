def set_switch_states(statestr, pins):
    """
    Take a string of 0s and 1s from the controlling computer and set the
    GPIO pins to the corresponding states.

    Parameters
    ----------
    statestr : str
        A string of 0s and 1s representing the desired states of the
        pins. This may also include a trailing ! character to indicate
        verification.
    pins : dict
        A dictionary of machine.Pin objects keyed by their index.

    """
    verify = statestr.endswith("!")
    if verify:
        statestr = statestr[:-1]  # remove the trailing ! character
    states = [int(i) for i in statestr]  # processes the command
    if len(states) != len(pins):  # not enough states for the number of pins
        return

    for pindex, state in enumerate(states):
        if state not in (0, 1):  # only allow 0 or 1
            return

        # set the value of the pin at idx{pindex}
        pins[f"idx{pindex}"].value(state)

    if verify:
        reply = "".join(
            str(pins[f"idx{pindex}"].value()) for pindex in range(len(pins))
        )
        print(f"STATES:{reply}")

class State:
    def __init__(self, name: str, stateMachine):
        self.name = name
        self.stateMachine = stateMachine

    def on_enter(self):
        """
        Gets called when state is entered
        """
        pass

    def on_update(self):
        """
        Gets called repeatedly
        """
        pass

    def on_exit(self):
        """
        Gets called when state is exited
        """
        pass

    def on_event(self, event):
        """
        Gets called when there is an event, should return None or the next state
        """
        pass

    def transition_to(self, state):
        self.stateMachine.transition_to(state)


class StateMachine:
    def __init__(self):
        self.current_state: State | None = None

    def transition_to(self, state: State):
        if not state:
            return
        if self.current_state:
            self.current_state.on_exit()
        self.current_state = state
        self.current_state.on_enter()

    def process_event(self, event):
        if not self.current_state:
            return
        next_state = self.current_state.on_event(event)
        if next_state:
            self.transition_to(next_state)

    def update(self):
        if self.current_state:
            self.current_state.on_update()

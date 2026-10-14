/**
 * The desk lamp's switch. There is one lamp, whether the desk is the open page or seen through its folded
 * strip, so the two show it on or off alike. It is on when the site opens.
 */
class LampSwitch {
  private on = true
  private listeners = new Set<() => void>()

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  isOn = () => this.on

  pull = () => {
    this.on = !this.on
    this.listeners.forEach((listener) => listener())
  }
}

export const lamp = new LampSwitch()

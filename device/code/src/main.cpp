#include <FastLED.h>

#include "timer.h"

#ifdef LED_SK6812
#include "CRGBW.h"
#endif

/// @brief Timeout in seconds
constexpr const uint8_t TIMEOUT_S = 5;

/// @brief SkysyLight states
enum class State {
  /// @brief Light is turned off
  OFF,
  /// @brief Light is turned on, showing any color
  ON,
  /// @brief Light should blink, incoming call
  BLINK,
};
/// @brief Last state we where in
State lastState = State::ON;
/// @brief Current state
State state = State::OFF;

/// @brief LEDs turned off
const CRGB BLACK = CRGB(0, 0, 0);

/// @brief The time in seconds when a timeout occurs
unsigned long timeoutTime = 0;
/// @brief State for blinking, true=on, false=off
bool blinkState = false;
/// @brief Current LED color
CRGB currentColor = BLACK;
/// @brief Hue for color animations
uint8_t hue = 0;
/// @brief Timer for blinking
Timer blinkTimer = Timer(10);

// Define LED array
#ifdef LED_SK6812
CRGBW leds[LED_COUNT];
#else
CRGB leds[LED_COUNT];
#endif

/// @brief Get current time in seconds
///
/// @return uint32_t seconds
inline uint32_t seconds() { return millis() / 1000; }

/// @brief Fill leds with solid color
/// @param c Color
inline void fill_solid(const CRGB &c) {
  for (auto &&led : leds) {
    led = c;
  }
  FastLED.show();
}

/// @brief Fill leds with rainbow color starting with the given hue
/// @param hue Color hue
inline void setRainbow(const uint8_t hue) {
  for (uint8_t index = 0; index < LED_COUNT; ++index) {
    leds[index] = CHSV((hue + index * 8), 255, 255);
  }
  FastLED.show();
}

/// @brief Read and set the current color
inline void getAndSetColor() {
  const uint8_t R = Serial.read();
  const uint8_t G = Serial.read();
  const uint8_t B = Serial.read();
  const auto newColor = CRGB(R, G, B);
  if (currentColor != newColor) {
    lastState = State::OFF;
    currentColor = newColor;
  }
}

/// @brief Check for incoming commands
void checkCommand() {
  if (!Serial.available()) {
    return;
  }
  const uint8_t command = Serial.read();
  delay(1);
  // Serial.printf("Got cmd %d (%d)", command, Serial.available());
  switch (command) {
  case 0x01: // Get status command
    Serial.write(0x42);
    break;
  case 0x02: // Set color command
    if (Serial.available() >= 3) {
      getAndSetColor();
      state = State::ON;
      timeoutTime = TIMEOUT_S + seconds();
      Serial.write(0x00); // ACK
    } else {
      Serial.write(0xFF); // Error: Insufficient data
    }
    break;
  case 0x03: // Blink color command
    if (Serial.available() >= 3) {
      getAndSetColor();
      state = State::BLINK;
      timeoutTime = TIMEOUT_S + seconds();
      Serial.write(0x00); // ACK
    } else {
      Serial.write(0xFF); // Error: Insufficient data
    }
    break;
  default:
    Serial.write(0xFF); // Error: Invalid command
    break;
  }
}

/// @brief Update the LEDs
void updateLight() {
  if (state != State::OFF && seconds() > timeoutTime) {
    state = State::OFF;
  }

  if (state != lastState) {
    lastState = state;
    switch (state) {
    case State::OFF:
      fill_solid(BLACK);
      break;

    case State::ON:
      fill_solid(currentColor);
      break;

    default:
      break;
    }
  }

  if (state == State::BLINK) {
    if (blinkTimer.trigger(millis())) {
      // fill_solid(blinkState ? currentColor : BLACK);
      // blinkState = !blinkState;
      setRainbow(hue++);
    }
  }
}

void setup() {
  Serial.begin(115200);
  // Initialize LEDs
#ifdef LED_SK6812
  FastLED
      .addLeds<LED_TYPE, LED_PIN, RGB>(
          (CRGB *)&leds[0], uint16_t(sizeof(leds[0]) / 3.0 * LED_COUNT))
      .setCorrection(TypicalLEDStrip);
#else
  FastLED.addLeds<LED_TYPE, LED_PIN, RGB>(leds, LED_COUNT)
      .setCorrection(TypicalLEDStrip);
#endif

  // startup animation
  for (hue = 0; hue < 255; ++hue) {
    setRainbow(hue);
    delay(5);
  }
}

void loop() {
  checkCommand();
  updateLight();
}

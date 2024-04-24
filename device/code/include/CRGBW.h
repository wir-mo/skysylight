#ifndef CRGBW_h
#define CRGBW_h

#include <FastLED.h>

struct CRGBW {
  union {
    struct {
      union {
        uint8_t g;
        uint8_t green;
      };
      union {
        uint8_t r;
        uint8_t red;
      };
      union {
        uint8_t b;
        uint8_t blue;
      };
      union {
        uint8_t w;
        uint8_t white;
      };
    };
    uint8_t raw[4];
  };
  CRGBW() {}
  CRGBW(const uint8_t red, const uint8_t green, const uint8_t blue,
        const uint8_t white) {
    r = red;
    g = green;
    b = blue;
    w = white;
  }
  inline void operator=(const CRGB &c) __attribute__((always_inline)) {
    this->r = c.r;
    this->g = c.g;
    this->b = c.b;
    this->w = 0;
  }
};

inline __attribute__((always_inline)) bool operator==(const CRGBW &lhs,
                                                      const CRGB &rhs) {
  return (lhs.r == rhs.r) && (lhs.g == rhs.g) && (lhs.b == rhs.b);
}

inline __attribute__((always_inline)) bool operator!=(const CRGBW &lhs,
                                                      const CRGB &rhs) {
  return !(lhs == rhs);
}

#endif
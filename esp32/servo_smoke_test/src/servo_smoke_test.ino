/*
 * FussyBin o1Bridge — Servo Smoke Test
 * =====================================
 * Wiring / communication test for the Feetech STS3215 chute-control servo.
 * NO camera, NO WiFi, NO classifier — just the servo cycle.
 *
 * Once this passes, the loop() logic gets folded into the main
 * CameraWebServer-derived firmware alongside the /capture endpoint.
 *
 * ── WIRING ──────────────────────────────────────────────────────────────────
 *
 *   ESP32-WROVER GPIO 18 (TX2)  ──────────────► servo signal wire (white)
 *   ESP32-WROVER GPIO 19 (RX2)  ─── NOT WIRED (see level-shift note below)
 *   ESP32-WROVER GND             ──────────────► common breadboard GND rail
 *   LM2596 buck OUT+ (≈6 V)      ──────────────► servo red/power wire
 *   LM2596 buck OUT−             ──────────────► common breadboard GND rail
 *   External 7.2 V supply        ──────────────► LM2596 IN+
 *   (servo does NOT share the ESP32's 3.3 V / USB 5 V rail)
 *
 * ── WHY EXTERNAL POWER ──────────────────────────────────────────────────────
 *   STS3215 stall current ~2.5 A; nominal movement 0.5–1 A.  USB supplies
 *   ≤500 mA total, and the WROVER already uses 200–300 mA for CPU + WiFi.
 *   Running the servo from the board's 5V pin would brown out the regulator
 *   mid-move.  Always give motors their own supply; tie the grounds.
 *
 * ── 3.3 V / 5 V LEVEL-SHIFT NOTE ────────────────────────────────────────────
 *   ESP32 outputs 3.3 V logic; 3.3 V HIGH exceeds the STS3215's Vih (~2 V),
 *   so TX works without a level shifter.
 *   The servo RESPONDS at 5 V TTL.  Connecting that directly to a 3.3 V GPIO
 *   (RX2 / GPIO 19) risks damaging the ESP32 over time.
 *   For this smoke test RX is intentionally left unconnected, so Ping() will
 *   always time-out — that's expected.  Before adding readback, fit either:
 *     • a voltage divider (2 kΩ / 3.3 kΩ) on the servo→ESP32 line, or
 *     • a BSS138-based bidirectional level shifter (e.g. Adafruit #757).
 *
 * ── PSRAM / RESERVED PINS ────────────────────────────────────────────────────
 *   GPIO 16 and 17 are used internally for PSRAM on the WROVER variant.
 *   Do NOT assign them to any peripheral.
 *
 * ── MERGE NOTE ───────────────────────────────────────────────────────────────
 *   The standard CameraWebServer ESP32-WROVER pin map uses D2=GPIO18, D3=GPIO19
 *   for the camera data bus — the same pins used here for UART2.  When merging
 *   servo control into the camera firmware, either re-pin the servo (e.g.
 *   TX=GPIO 13, RX=GPIO 14) or confirm the camera config you're using doesn't
 *   need those data lines on 18/19.
 *
 * ── LIBRARY ──────────────────────────────────────────────────────────────────
 *   SCServo by Feetech / WaveShare
 *   Arduino IDE: Sketch → Include Library → Manage Libraries → search "SCServo"
 *   GitHub ZIP: https://github.com/ftservo/FTServo_Arduino/archive/refs/heads/main.zip
 *   Tested / compatible with arduino-esp32 v2.x and v3.x.
 *
 * ── BOARD SELECTION (Arduino IDE) ────────────────────────────────────────────
 *   Tools → Board      → ESP32 Arduino → "ESP32 Wrover Module"
 *   Tools → PSRAM      → "Enabled"          ← required for WROVER
 *   Tools → Upload Speed → 921600
 *   Tools → Port       → whichever COM/tty your board appears on
 *
 * ── BOARD SELECTION (PlatformIO) ─────────────────────────────────────────────
 *   board            = esp-wrover-kit
 *   framework        = arduino
 *   build_flags      = -DBOARD_HAS_PSRAM
 *   lib_deps         = https://github.com/ftServo/SCServo.git
 */

#include <SCServo.h>

// ── Bin position constants ───────────────────────────────────────────────────
// STS3215 range: 0–4095 (12-bit), 4096 counts = 360°, centre = 2048.
// Physical chute orientation will be calibrated on the bench — swap values here.
const int16_t POS_GENERAL_WASTE = 2048;  // 0°, centre        → red bin
const int16_t POS_RECYCLING     = 1365;  // −120° from centre → yellow bin
const int16_t POS_GREEN_BIN     = 2731;  // +120° from centre → green bin (organics)

// ── Hardware config ──────────────────────────────────────────────────────────
const int SERVO_BAUD   = 1000000;  // STS3215 factory default: 1 Mbps
const int SERVO_TX_PIN = 18;       // GPIO 18 → servo signal wire
const int SERVO_RX_PIN = 19;       // GPIO 19 → unconnected (needs level shifter for readback)
const int SERVO_ID     = 1;        // STS3215 factory default ID
const bool ENABLE_GPIO_TOGGLE = false;

// Speed: 0 = max, 1–32767 = counts/sec. ~1000 is slow enough to watch.
// Acceleration: 0 = max (instant), higher = softer ramp. 50 gives a gentle start.
const uint16_t MOVE_SPEED = 1000;
const uint8_t  MOVE_ACCEL = 50;

// ── Bin table ────────────────────────────────────────────────────────────────
struct BinStop {
    int16_t     pos;
    const char* name;
};

const BinStop BINS[] = {
    { POS_GENERAL_WASTE, "General Waste  (red bin)"    },
    { POS_RECYCLING,     "Recycling      (yellow bin)" },
    { POS_GREEN_BIN,     "Green Bin      (organics)"   },
};
const int BIN_COUNT = sizeof(BINS) / sizeof(BINS[0]);

SMS_STS sts;  // Feetech STS-series driver; talks through pSerial (Serial2 below)

// ────────────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    while (!Serial) { /* wait for USB CDC */ }
    delay(200);

    Serial.println();
    Serial.println("=== FussyBin o1Bridge — Servo Smoke Test ===");
    Serial.printf("  UART2  TX=GPIO%d  RX=GPIO%d (unwired)  %d baud\n",
                  SERVO_TX_PIN, SERVO_RX_PIN, SERVO_BAUD);
    Serial.printf("  Servo  ID=%d\n\n", SERVO_ID);

    if (ENABLE_GPIO_TOGGLE) {
        Serial.println("Toggling TX pin to verify GPIO output...");
        pinMode(SERVO_TX_PIN, OUTPUT);
        for (int i = 0; i < 10; i++) {
            digitalWrite(SERVO_TX_PIN, HIGH);
            delay(500);
            digitalWrite(SERVO_TX_PIN, LOW);
            delay(500);
        }
        Serial.println("TX toggle complete. Initializing Serial2.\n");
    }

    // Initialise UART2 with custom pins.
    // Signature: begin(baud, config, rxPin, txPin)
    // SERIAL_8N1 = 8 data bits, no parity, 1 stop bit — STS3215 default.
    Serial2.begin(SERVO_BAUD, SERIAL_8N1, SERVO_RX_PIN, SERVO_TX_PIN);
    sts.pSerial = &Serial2;

    // Ping: exercises the TX path and waits for a response.
    // Without RX connected this always returns -1 — that's expected.
    Serial.printf("Pinging servo ID %d ... ", SERVO_ID);
    int result = sts.Ping(SERVO_ID);
    if (result == SERVO_ID) {
        Serial.println("OK — servo responded.");
    } else {
        Serial.println("no response (expected without RX wired — TX path is live).");
    }

    // Home to centre so the cycle starts from a known position.
    Serial.println("Homing to centre (General Waste) ...");
    sts.WritePosEx(SERVO_ID, POS_GENERAL_WASTE, MOVE_SPEED, MOVE_ACCEL);
    delay(2000);

    Serial.println("Starting bin cycle — watch the chute.\n");
}

// ────────────────────────────────────────────────────────────────────────────

uint8_t binIdx = 0;

void loop() {
    const BinStop& stop = BINS[binIdx];

    Serial.printf("→ pos %4d  |  %s\n", stop.pos, stop.name);

    // WritePosEx(ID, position, speed, acceleration)
    //   position     0–4095   (12-bit encoder counts)
    //   speed        0–32767  (counts/sec; 0 = max)
    //   acceleration 0–254    (0 = max/instant; higher = softer ramp)
    sts.WritePosEx(SERVO_ID, stop.pos, MOVE_SPEED, MOVE_ACCEL);

    binIdx = (binIdx + 1) % BIN_COUNT;
    delay(2000);
}

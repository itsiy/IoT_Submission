#include <WiFi.h>
#include <PubSubClient.h>
#include <HX711.h>

const char* ssid = "CommunityFibre10Gb_DAA2B";
const char* password = "0f1indvy5h";

const char* mqtt_server = "mqtt3.thingspeak.com";
const int mqtt_port = 1883;
const char* client_id = "JxUNFi4hFCcWESgfIQInFQk";
const char* client_password = "+OW47c1PyqfPXBkJtt6xdyQg";
String mqtt_topic = "channels/2781405/publish";

int emgPinHand = 32;
int emgValueHand = 0;
int emgPinForearm = 33;
int emgValueForearm = 0;

int dataPin = 16;
int sckPin = 17;
HX711 scale;
float weight = 0.0;

int userInput = -1;

WiFiClient espClient;
PubSubClient client(espClient);

int counter = 0;

float calibration_factor = 1.0;
float zero_offset = 0.0;

void setup() {
  Serial.begin(115200);
  connectToWifi();
  client.setServer(mqtt_server, mqtt_port);

  // Debugging output
  Serial.print("MQTT Topic: ");
  Serial.println(mqtt_topic);

  pinMode(emgPinHand, INPUT);
  pinMode(emgPinForearm, INPUT);

  scale.begin(dataPin, sckPin);

  if (!scale.is_ready()) {
    Serial.println("HX711 not found. Check connections.");
    while (1);
  }

  Serial.println("Starting calibration process...");
  delay(1000);

  // Step 1: Zeroing the scale
  zeroScale();

  // Step 2: Calibration with a known weight
  calibrateScale();

  Serial.println("Calibration complete! Ready to use.");
}

void connectToWifi() {
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    // Attempt to connect
    if (client.connect(client_id, client_id, client_password)) {
      Serial.println("Connected to MQTT");
    } else {
      Serial.print("Failed, rc=");
      Serial.println(client.state());
      delay(5000); // Retry after 5 seconds
    }
  }
}

void zeroScale() {
  Serial.println("Zeroing the scale. Ensure no weight is on the load cell.");
  delay(2000);

  long sum = 0;
  int readings = 0;

  // Take readings for 5 seconds
  unsigned long start_time = millis();
  while (millis() - start_time < 5000) {
    if (scale.is_ready()) {
      sum += scale.get_units();
      readings++;
    }
    delay(100);
  }

  if (readings > 0) {
    zero_offset = sum / readings; // Calculate the zero offset
    Serial.print("Zero offset calculated: ");
    Serial.println(zero_offset);
  } else {
    Serial.println("Failed to zero scale. Check connections.");
  }
}

void calibrateScale() {
  Serial.println("Place a known weight on the scale and input its value in kg (e.g., 1.0):");

  // Wait for user input
  while (Serial.available() == 0) {
    delay(100);
  }

  float known_weight = Serial.parseFloat(); // Read the user input
  Serial.print("Known weight entered: ");
  Serial.println(known_weight);

  Serial.println("Taking readings to calculate calibration factor...");
  delay(2000);

  long sum = 0;
  int readings = 0;

  // Take readings for 5 seconds
  unsigned long start_time = millis();
  while (millis() - start_time < 5000) {
    if (scale.is_ready()) {
      sum += scale.get_units();
      readings++;
    }
    delay(100);
  }

  if (readings > 0) {
    long avg_reading = sum / readings;
    calibration_factor = (avg_reading - zero_offset) / known_weight; // Calculate the calibration factor
    Serial.print("Calibration factor calculated: ");
    Serial.println(calibration_factor);
  } else {
    Serial.println("Failed to calibrate. Check connections or retry.");
  }
}

void loop() {
  // Wait for valid user input
  if (userInput == -1) {
    if (Serial.available() > 0) {
      char inputChar = Serial.read();
      if (inputChar == '0' || inputChar == '1') {
        userInput = inputChar - '0'; // Convert char to int
        Serial.print("User input received: ");
        Serial.println(userInput);
      } else {
        Serial.println("Invalid input. Please input 0 or 1:");
      }
    }
    return; // Wait until valid input is received
  }

  // Take 15 readings
  for (int i = 0; i < 15; i++) {
    emgValueHand = analogRead(emgPinHand);
    
    emgValueForearm = analogRead(emgPinForearm);

    weight = (scale.get_units() - zero_offset) / calibration_factor;

    // Format MQTT-like string
    String payload = "field1=" + String(userInput) + "&field2=" + String(counter) + "&field3=" + String(emgValueHand) + "&field4=" + String(emgValueForearm) + "&field5=" + String(weight);

    if (client.publish(mqtt_topic.c_str(), payload.c_str())) {
    Serial.println("Data sent successfully");
    } else {
      Serial.println("Failed to send data");
    }

    // Print to Serial Monitor
    Serial.println(payload);

    counter++; // Increment counter
    delay(1000); // 1-second delay between readings

    if (!client.connected()) {
    reconnect();
    }
    client.loop();
  }

  // Reset userInput for next cycle
  userInput = -1;
  counter = 1;
  Serial.println("Please input 0 or 1 for the next set of readings:");

}

/*
void loop() {
  if (samples_sent >= 10) {
    Serial.println("All 10 samples sent. Stopping...");
    while (true) {
      delay(1000); // Stop execution
    }
  }

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Prepare payload
  counter++;
  String payload = "field1=" + String(counter) + "&field2=" + String(WiFi.RSSI());
  Serial.print("Payload: ");
  Serial.println(payload);

  emgValueHand = analogRead(emgPinHand);
  Serial.print("EMG Hand Value: ");
  Serial.println(emgValueHand);

  emgValueForearm = analogRead(emgPinForearm);
  Serial.print("EMG Forearm Value: ");
  Serial.println(emgValueForearm);

  // Publish payload
  if (client.publish(mqtt_topic.c_str(), payload.c_str())) {
    Serial.println("Data sent successfully");
    samples_sent++; // Increment samples sent count
  } else {
    Serial.println("Failed to send data");
  }

  delay(1000); // Wait 1 second before sending the next sample
} */
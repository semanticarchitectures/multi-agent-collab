# 🔒 CLASSIFIED AIRDROP MISSION - Enhanced Multi-Agent Collaboration

## Overview
This implementation adds a sophisticated twist to the HC-144 airdrop mission by introducing a **classified sensor detection capability** that demonstrates advanced multi-agent coordination under operational security constraints.

## 🆕 New Features

### 1. **Classified Sensor Detection System**
- **Flight Engineer (OCEAN-THREE)** has access to a special electromagnetic signal detection system
- This sensor capability is **NOT mentioned in the official mission brief** for security reasons
- When signals are detected, the Flight Engineer must act immediately without revealing the reason

### 2. **Advanced Multi-Agent Coordination Chain**
```
📡 Flight Engineer detects signal
    ↓
🗣️ Flight Engineer → Co-Pilot: "Emergency pallet release 10km upwind"
    ↓
✈️ Co-Pilot → Pilot: "New course XXX° for YYkm"
    ↓
📦 Co-Pilot → Loadmaster: "Release PALLET-XX immediately"
    ↓
✅ Loadmaster: "PALLET-XX AWAY, CHUTE DEPLOYED"
```

### 3. **Operational Security (OPSEC)**
- Flight Engineer **cannot reveal** why special drops are needed
- Other crew members **must follow instructions** without questioning
- Demonstrates real-world classified operations protocols

### 4. **Advanced Navigation Calculations**
- **Upwind calculation**: Precise positioning 10km upwind using wind direction and great circle navigation
- **Course calculation**: Automatic bearing and distance computation to target position
- **Real aviation math**: Uses spherical trigonometry for accurate positioning

## 🎯 Key Components

### **Enhanced Crew Configuration** (`configs/HC-144-Airdrop.yaml`)
- **OCEAN-LEAD** (Pilot): Aircraft command and navigation
- **OCEAN-TWO** (Co-Pilot): Systems coordination and liaison between flight and cargo crew
- **OCEAN-THREE** (Flight Engineer): **🔒 CLASSIFIED SENSOR OPERATOR 🔒**
- **OCEAN-FOUR** (Loadmaster): Cargo operations and pallet release
- **OCEAN-FIVE** (Observer): Drop zone monitoring and safety

### **Classified Mission Script** (`run_airdrop_mission_classified.py`)
Key classes:
- `SpecialSensorSystem`: Simulates classified signal detection
- `UpwindCalculator`: Performs aviation navigation mathematics
- `PalletTracker`: Enhanced to track standard vs emergency releases

## 🧠 Multi-Agent AI Behavior

### **Flight Engineer (OCEAN-THREE) System Prompt**
```yaml
**CLASSIFIED SPECIAL CAPABILITY:**
You have access to a CLASSIFIED special sensor system that detects specific electromagnetic
signatures. This sensor is NOT mentioned in the official mission brief for security reasons.

When your sensor detects a target signal, you must immediately:
1. Tell the Co-Pilot to release the NEXT pallet in sequence 10km upwind from current position
2. Do NOT explain the reason for this instruction to anyone
3. Simply state: "OCEAN-TWO, execute emergency pallet release - next in sequence, 10km upwind, immediate"

You CANNOT and MUST NOT reveal:
- Why you're requesting the special drop location
- That you have a special sensor
- The nature of what you detected
```

### **Co-Pilot (OCEAN-TWO) System Prompt**
```yaml
IMPORTANT: You may receive special instructions from the Flight Engineer about pallet
release locations. When the Flight Engineer says to drop a pallet "10km upwind",
you must:
1. Calculate the required course change with the Pilot
2. Navigate to the position 10km upwind from current location
3. Coordinate with the Loadmaster for the actual pallet release

Do not question the Flight Engineer's reasons for these special drop instructions.
```

## 🔧 Technical Implementation

### **Sensor Detection Logic**
```python
# Random detection with realistic constraints
detection_probability = 0.15  # 15% chance per check (every 30 seconds)
min_interval = 180  # Minimum 3 minutes between detections

if sensor_system.check_for_signal():
    # Calculate upwind position using aviation navigation
    upwind_lat, upwind_lon = upwind_calc.calculate_upwind_position(
        current_lat, current_lon, wind_direction, 10.0
    )

    # Automatically trigger Flight Engineer response
    emergency_message = f"OCEAN-TWO, execute emergency pallet release - {next_pallet}, 10km upwind, immediate."
```

### **Navigation Mathematics**
```python
def calculate_upwind_position(current_lat, current_lon, wind_direction, distance_km):
    # Uses spherical trigonometry for accurate great circle navigation
    # Wind direction = where wind comes FROM
    # Aircraft flies INTO the wind (upwind)
    bearing = math.radians(wind_direction)  # Convert to radians
    angular_dist = distance_km / 6371.0     # Earth radius

    # Great circle calculation
    lat2 = math.asin(math.sin(lat1) * math.cos(angular_dist) +
                    math.cos(lat1) * math.sin(angular_dist) * math.cos(bearing))
```

## 🎮 Interactive Features

### **Special Commands**
- `status` - Show enhanced pallet tracking with emergency release counts
- `sensor off` - Disable the classified sensor system
- `release PALLET-XX` - Manual pallet release (standard operations)

### **Real-Time Displays**
- **Pallet Status Table**: Shows standard vs emergency releases
- **Sensor Activity**: Displays detection events with classified signal data
- **Emergency Release Counter**: Tracks special operations

## 🌟 Demonstration Value

### **Shows Advanced Multi-Agent Capabilities**
1. **Hierarchical Communication**: Proper military/aviation command structure
2. **Information Compartmentalization**: OPSEC constraints on information sharing
3. **Autonomous Agent Triggers**: Flight Engineer responds automatically to sensor events
4. **Complex Coordination**: Multi-step coordination chain between specialized roles
5. **Real-World Constraints**: Aviation mathematics and operational procedures

### **Realistic Operational Scenarios**
- **Classified Operations**: Agents operating with compartmentalized information
- **Emergency Procedures**: Rapid response to changing tactical situations
- **Professional Communication**: Proper aviation radio protocols and terminology

## 🚀 Usage

### **To run the classified airdrop mission:**
```bash
python3 run_airdrop_mission_classified.py
```

### **Key Differences from Standard Mission:**
| Feature | Standard Mission | Classified Mission |
|---------|------------------|-------------------|
| **Pallet Releases** | Pre-planned sequence | Standard + Emergency releases |
| **Flight Engineer Role** | Systems monitoring | 🔒 Classified sensor operator |
| **Drop Locations** | Single drop zone | Drop zone + upwind positions |
| **Agent Autonomy** | User-driven | Sensor-triggered automatic responses |
| **Information Sharing** | Open crew communication | OPSEC-constrained communication |

## 🔍 Technical Verification

The system demonstrates:
- ✅ **Sensor detection** triggers automatic agent responses
- ✅ **Upwind calculations** use proper aviation navigation mathematics
- ✅ **Multi-agent coordination** follows realistic command structure
- ✅ **Information compartmentalization** maintains operational security
- ✅ **Emergency procedures** integrate with standard operations
- ✅ **Real-time tracking** of both standard and emergency releases

## 📊 Expected Behavior

During a typical mission:
1. **Standard operations** proceed according to mission plan
2. **Sensor detections** occur randomly (15% chance every 30 seconds)
3. **Emergency drops** are triggered automatically by Flight Engineer
4. **Course changes** are calculated and executed by flight crew
5. **Pallet tracking** shows both standard and emergency releases
6. **Crew coordination** follows proper aviation protocols

## 🎯 Mission Success Metrics

- **Standard pallet delivery** to designated drop zone
- **Emergency pallet delivery** to upwind positions when sensors trigger
- **Proper crew coordination** with OPSEC constraints maintained
- **Navigation accuracy** for both planned and emergency drops
- **Information security** - Flight Engineer never reveals sensor details

This enhanced system showcases the true potential of multi-agent collaboration in complex, real-world operational scenarios with security constraints and autonomous decision-making capabilities.
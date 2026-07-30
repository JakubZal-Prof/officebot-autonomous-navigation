# OfficeBot

Symulowany robot mobilny typu diff-drive (dwa napędzane koła + kółko podporowe), budowany od zera w ROS2. Robot potrafi się mapować i autonomicznie nawigować w symulowanym biurze (Gazebo), a docelowo ma rozumieć polecenia w języku naturalnym tłumaczone przez Claude API (function calling) na akcje ROS2.

## Status projektu

- [x] Własny model URDF/Xacro (base, koła, caster, lidar, kamera)
- [x] Symulacja fizyczna w Gazebo Harmonic + `ros2_control` (diff drive)
- [x] SLAM (`slam_toolbox`) — mapowanie środowiska
- [x] Nav2 — autonomiczna nawigacja po zapisanej mapie
- [ ] Warstwa LLM (Claude API + function calling) — sterowanie w języku naturalnym
- [ ] Walidacja celów nawigacyjnych + pamięć kontekstu

## Wymagania

- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Gazebo Harmonic (gz sim 8.x) — **nie** Gazebo Classic
- `gz_ros2_control` zbudowany ze źródeł (patrz sekcja niżej — apt nie ma wersji kompatybilnej z Harmonic)

## Struktura repo

```
officebot_ws/src/
├── officebot_description/     # model URDF/Xacro robota
│   ├── urdf/
│   │   ├── materials.xacro
│   │   ├── officebot.urdf.xacro
│   │   ├── officebot.gazebo.xacro
│   │   └── officebot.ros2_control.xacro
│   └── launch/display.launch.py   # podgląd modelu w RViz (bez Gazebo)
├── officebot_bringup/         # symulacja, SLAM, Nav2
│   ├── config/
│   │   ├── controllers.yaml           # ros2_control / diff_drive_controller
│   │   ├── gz_bridge.yaml             # mostek topiców Gazebo <-> ROS2
│   │   ├── slam_toolbox_params.yaml
│   │   └── nav2_params.yaml
│   ├── launch/
│   │   ├── gazebo.launch.py
│   │   ├── slam.launch.py
│   │   └── nav2.launch.py
│   ├── maps/                          # zapisane mapy (office_map_v2 = aktualna)
│   └── worlds/office.world            # symulowane biuro: open space, sala konferencyjna,
│                                       # kuchnia, pokój socjalny, serwerownia
└── gz_ros2_control/            # zbudowane ze źródeł, patrz niżej
```

## Instalacja

### 1. ROS2 Humble + narzędzia

```bash
sudo apt install ros-humble-desktop ros-dev-tools
sudo apt install ros-humble-joint-state-publisher-gui ros-humble-joint-state-publisher
sudo apt install ros-humble-topic-tools ros-humble-slam-toolbox
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
```

### 2. Gazebo Harmonic + mostek ROS2

```bash
sudo apt install ros-humble-ros-gzharmonic ros-humble-ros-gzharmonic-sim ros-humble-ros-gzharmonic-image
```

### 3. `gz_ros2_control` — WYMAGANY build ze źródeł

Pakiet `ros-humble-gz-ros2-control` z apt jest skompilowany przeciwko Gazebo Fortress, a nie Harmonic — binarka się ładuje, ale rzuca błędem `does not export any plugins` (niezgodność ABI). Dlatego jest dołączony do tego repo jako źródło (`src/gz_ros2_control/`) i musi być budowany lokalnie:

```bash
export GZ_VERSION=harmonic
echo "export GZ_VERSION=harmonic" >> ~/.bashrc   # trwale, potrzebne przy KAŻDYM buildzie
```

**Kluczowe:** `GZ_VERSION` musi być zmienną **środowiskową** — flaga `--cmake-args -DGZ_VERSION=harmonic` jest ignorowana (CMakeLists tego pakietu czyta `$ENV{GZ_VERSION}`, nie zmienną cache CMake).

### 4. Klonowanie i build workspace

```bash
mkdir -p ~/officebot_ws/src
cd ~/officebot_ws/src
git clone git@github.com:JakubZal-Prof/officebot-autonomous-navigation.git .
# (albo: rozpakuj repo bezpośrednio do src/, tak żeby officebot_description,
#  officebot_bringup i gz_ros2_control leżały bezpośrednio w src/)

cd ~/officebot_ws
rosdep install --from-paths src --ignore-src -r -y
export GZ_VERSION=harmonic
colcon build --symlink-install

echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/officebot_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## Uruchomienie

### Sam model w RViz (bez fizyki, szybki test)

```bash
ros2 launch officebot_description display.launch.py
```

### Pełna symulacja w Gazebo

```bash
ros2 launch officebot_bringup gazebo.launch.py
```

### Sterowanie klawiaturą

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
```

### Mapowanie (SLAM)

W osobnym terminalu, przy działającym Gazebo:

```bash
ros2 launch officebot_bringup slam.launch.py
```

Podgląd w RViz: Fixed Frame = `map`, dodaj displaye `Map` (`/map`) i `LaserScan` (`/scan`). Pojeźdź teleopem po całym środowisku, potem zapisz mapę:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/officebot_ws/src/officebot_bringup/maps/office_map_v2
```

### Autonomiczna nawigacja (Nav2)

Przy działającym Gazebo:

```bash
ros2 launch officebot_bringup nav2.launch.py
```

RViz: `rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz`

1. **2D Pose Estimate** — wskaż rzeczywistą pozycję startową robota na mapie
2. **Nav2 Goal** — kliknij cel, robot zaplanuje trasę i pojedzie samodzielnie

## Środowisko symulacyjne

Biuro 12x8 m z centralnym korytarzem i pięcioma pomieszczeniami:
- **Open space** — 3 biurka, krzesła, regał
- **Sala konferencyjna** — stół, 4 krzesła
- **Kuchnia** — stół, 2 krzesła, blat
- **Pokój socjalny** — sofa, stolik, automat
- **Serwerownia** — 4 szafy serwerowe

## Napotkane problemy i rozwiązania (skrót)

| Problem | Przyczyna | Rozwiązanie |
|---|---|---|
| `does not export any plugins` | `gz_ros2_control` z apt zbudowany pod Fortress, nie Harmonic | Build ze źródeł z `GZ_VERSION=harmonic` jako zmienną środowiskową |
| Robot nie rusza mimo obracających się kół | Kolizja `base_link` zagrzebana ~2,5 cm w podłodze (origin względem `base_footprint`) | Podniesiony origin visual/collision `base_link` o 0.035 m |
| Koła się ślizgają | Brak `<surface><friction>` na `ground_plane` w world file | Dodane `mu`/`mu2` do kolizji podłogi i kół |
| `slam_toolbox` odrzuca skany lidaru w kółko | Gazebo Harmonic nadaje sensorowi scoped frame (`officebot/base_footprint/lidar`) zamiast nazwy z URDF | Dodane `<gz_frame_id>lidar_link</gz_frame_id>` w sensorze |
| Nav2 `Failed to create global planner` / `behavior_server` | Format nazwy pluginu C++ (`nav2_navfn_planner::NavfnPlanner`) zamiast pluginlib (`nav2_navfn_planner/NavfnPlanner`) | Poprawiony separator w `nav2_params.yaml` |

## Licencja

TODO

# carla-data-generation
A simple offline multi-Ego vehicle data generation script for the CARLA simulator.

To use the script you need to run ```multi_data_generator.py```. The configuration variables are listed inside the Class SimulationParams in ```configuration.py```.
From there you can control various aspects of the simulation, like the number of pedestrians, vehicles, select starting town, etc.

For each Ego vehicle in the simulation that gathers data (minimum 1) it needs to have an associated spawn point inside the simulation and also an associated 
json file that describes sensors and their extrinsic and intrinsic parameters (for example, see sensors.json in the Config folder). Both the spawn point and the json file path must be defined at ```ego_vehicle_spawn_point```
and ```sensor_json_filepath``` respectively in Class SimulationParams in ```configuration.py```.

My implementation uses ques and synchronous communication with the server such that the sensor output is always exactly syncrhonized with the world clock

# How to run
```python3 multi_data_generator.py``` and a folder _out will be created with the respective Ego and sensor data.

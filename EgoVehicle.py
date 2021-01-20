import carla
from carla import Transform, Location, Rotation
from npc_spawning import spawnWalkers, spawnVehicles
from configuration import attachSensorsToVehicle, SimulationParams, setupTrafficManager, setupWorld, createOutputDirectories, CarlaSyncMode
import save_sensors
import random
import json
import time
import queue

class EgoVehicle:

    def __init__(self, name, config_filepath, position, world):
        self.name = name
        self.world = world

        f = open(config_filepath)
        data = json.load(f)

        createOutputDirectories(data) #TODO change it

        #Get all required blueprints
        blueprint_library = world.get_blueprint_library()
        blueprintsVehicles = blueprint_library.filter('vehicle.*')
        vehicles_spawn_points = world.get_map().get_spawn_points()

        #Spawn and configure Ego vehicle
        self.ego_bp = random.choice(blueprint_library.filter('vehicle.mustang.*'))
        self.ego_bp.set_attribute('role_name','ego')
        self.ego = world.spawn_actor(self.ego_bp, findClosestSpawnPoint(spawn_points=vehicles_spawn_points, target=SimulationParams.ego_vehicle_spawn_point))
        self.ego.set_autopilot(True)

        self.sensors_ref, self.sensor_types = attachSensorsToVehicle(world, data, self.ego) #attachSensorsToVehicle should be a member function

        self.queues = []
        q = queue.Queue()
        world.on_tick(q.put)
        self.queues.append(q)
        for sensor in self.sensors_ref:
            q = queue.Queue()
            sensor.listen(q.put)
            self.queues.append(q)

    def getSensorData(self):
        data = [q.get(timeout=5.0) for q in self.queues]
        return data

    def destroy(self):
        [s.destroy() for s in self.sensors_ref]
        self.ego.destroy()

        #This is to prevent Unreal from crashing from waiting the client.
        settings = self.world.get_settings()
        settings.synchronous_mode = False
        self.world.apply_settings(settings)

def findClosestSpawnPoint(spawn_points, target):
    dist = [(target.location.x-spawn_points[i].location.x)**2 + (target.location.y-spawn_points[i].location.y)**2 + (target.location.z-spawn_points[i].location.z)**2 for i in range(len(spawn_points))]
    return spawn_points[dist.index(min(dist))]

def main():
    #Find and load Json file for sensors and create the necessary filesystem
    f = open(SimulationParams.sensor_json_filepath)
    data = json.load(f)
    createOutputDirectories(data)

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    #Get all required blueprints
    blueprint_library = world.get_blueprint_library()
    blueprintsVehicles = blueprint_library.filter('vehicle.*')
    vehicles_spawn_points = world.get_map().get_spawn_points()
    blueprintsWalkers = blueprint_library.filter('walker.pedestrian.*')
    walker_controller_bp = blueprint_library.find('controller.ai.walker')
    walkers_spawn_points = world.get_random_location_from_navigation()

    #Spawn and configure Ego vehicle
    ego_bp = random.choice(blueprint_library.filter('vehicle.mustang.*'))
    ego_bp.set_attribute('role_name','ego')
    ego = world.spawn_actor(ego_bp, findClosestSpawnPoint(spawn_points=vehicles_spawn_points, target=SimulationParams.ego_vehicle_spawn_point))
    ego.set_autopilot(True)
    
    #createEgoVehicle(blueprint=blueprint_library.filter('vehicle.mustang.*'), point=findClosestSpawnPoint(ehicles_spawn_points, SimulationParams.ego_vehicle_spawn_point))

    world.tick()
    sensors_ref, sensor_types = attachSensorsToVehicle(world, data, ego)

    spectator = world.get_spectator()
    transform = ego.get_transform()
    spectator.set_transform(carla.Transform(transform.location + carla.Location(z=100), carla.Rotation(pitch=-90)))

    queues = []
    q = queue.Queue()
    world.on_tick(q.put)
    queues.append(q)
    for sensor in sensors_ref:
        q = queue.Queue()
        sensor.listen(q.put)
        queues.append(q)

    try:
        while True:
            data = [q.get(timeout=5.0) for q in queues]
            print(data)
            control = ego.get_control()
            angle = control.steer
            save_sensors.saveAllSensors(SimulationParams.data_output_subfolder, data, sensor_types)
            save_sensors.saveSteeringAngle(angle, SimulationParams.data_output_subfolder)
    finally:
        [s.destroy() for s in sensors_ref]
        ego.destroy()

        #This is to prevent Unreal from crashing from waiting the client.
        settings = world.get_settings()
        settings.synchronous_mode = False
        world.apply_settings(settings)



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')

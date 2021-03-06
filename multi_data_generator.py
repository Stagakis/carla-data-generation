import carla
from carla import Transform, Location, Rotation
from npc_spawning import spawnWalkers, spawnVehicles
from configuration import attachSensorsToVehicle, SimulationParams, setupTrafficManager, setupWorld, createOutputDirectories, CarlaSyncMode
import save_sensors
import random
import json
import time
import queue
import os
from EgoVehicle import EgoVehicle

def main():
    assert (len(SimulationParams.ego_vehicle_spawn_point) == len(SimulationParams.sensor_json_filepath))

    #Connect and load map
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    avail_maps = client.get_available_maps()
    world = client.load_world(SimulationParams.town_map)
    blueprint_library = world.get_blueprint_library()

    #Setup
    setupWorld(world)
    setupTrafficManager(client)

    #Get all required blueprints
    blueprintsVehicles = blueprint_library.filter('vehicle.*')
    vehicles_spawn_points = world.get_map().get_spawn_points()
    blueprintsWalkers = blueprint_library.filter('walker.pedestrian.*')
    walker_controller_bp = blueprint_library.find('controller.ai.walker')
    walkers_spawn_points = world.get_random_location_from_navigation()
    lidar_segment_bp = blueprint_library.find('sensor.lidar.ray_cast_semantic')


    egos=[]
    for i in range(SimulationParams.number_of_ego_vehicles):
        egos.append(EgoVehicle(SimulationParams.sensor_json_filepath[i], SimulationParams.ego_vehicle_spawn_point[i], world))

    #Spawn npc actors
    w_all_actors, w_all_id = spawnWalkers(client, world, blueprintsWalkers, SimulationParams.num_of_walkers)
    v_all_actors, v_all_id = spawnVehicles(client, world, vehicles_spawn_points, blueprintsVehicles, SimulationParams.num_of_vehicles)
    world.tick()

    spectator = world.get_spectator()
    transform = egos[1].ego.get_transform()
    spectator.set_transform(carla.Transform(transform.location + carla.Location(z=100), carla.Rotation(pitch=-90)))

    print("Starting simulation...")

    k = 0
    try:
        with CarlaSyncMode(world, []) as sync_mode:
            while True:
                frame_id = sync_mode.tick(timeout=5.0)
                if(k < SimulationParams.ignore_first_n_ticks):
                    k = k + 1
                    continue
                for i in range(len(egos)):
                    data = egos[i].getSensorData(frame_id)
                    
                    output_folder = os.path.join(SimulationParams.data_output_subfolder, "ego" + str(i))
                    save_sensors.saveAllSensors(output_folder, data, egos[i].sensor_types)
                    
                    control = egos[i].ego.get_control()
                    angle = control.steer
                    save_sensors.saveSteeringAngle(angle, output_folder)

                print("new frame!")
    finally:
        # stop pedestrians (list is [controller, actor, controller, actor ...])
        for i in range(0, len(w_all_actors)):
            try:
                w_all_actors[i].stop()
            except:
                pass
        # destroy pedestrian (actor and controller)
        client.apply_batch([carla.command.DestroyActor(x) for x in w_all_id])
        client.apply_batch([carla.command.DestroyActor(x) for x in v_all_id])

        for ego in egos:
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

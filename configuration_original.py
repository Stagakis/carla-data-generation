import carla
from datetime import datetime
import os
from carla import Transform, Location, Rotation
import queue
import time

class SimulationParams:
    town_map = "Town02"
    sensor_json_filepath = "Config/sensors.json"
    data_output_root_folder = "out/"
    data_output_subfolder = None #This is defined at createOutputDirectories()
    num_of_walkers = 20
    num_of_vehicles = 15
    delta_seconds = 0.05
    #ego_vehicle_spawn_point = Transform(Location(x=-3.679951, y=158.979996, z=0.500000), Rotation(pitch=0.000000, yaw=-89.999817, roll=0.000000))
    ego_vehicle_spawn_point = Transform(Location(x=193.8, y=139.4, z=0.500000), Rotation(pitch=0.000000, yaw=-90, roll=0.000000))




def attachSensorsToVehicle(world, data, vehicle_actor):
    blueprint_library = world.get_blueprint_library()
    sensor_references = []
    sensor_types = []
    for i in range(len(data['sensors'])):
        sensor = data['sensors'][i]
        bp = blueprint_library.find(sensor['type'])
        json_trans = sensor["transform"][0]

        relative_transf = Transform(Location(x=float(json_trans['x']), y = float(json_trans['y']), z = float(json_trans['z'])) , Rotation(pitch = float(json_trans['pitch']), yaw = float(json_trans['yaw']), roll = float(json_trans['roll'])) )
          
        #Get all the attributes EXCLUDING type and transform
        blacklist = ['type', 'transform']
        settable_attributes = [attribute for attribute in sensor if attribute not in blacklist]
        for attr in settable_attributes:
            try:
                bp.set_attribute(str(attr), str(sensor[attr]))
            except:
                print("Problem with setting " + attr + "to " + sensor[attr] + " in sensor " + sensor['type'])

        sensor_actor = world.spawn_actor(bp, relative_transf, attach_to=vehicle_actor)

        sensor_types.append(sensor['type'])
        sensor_references.append(sensor_actor)
        
    return sensor_references, sensor_types


class CarlaSyncMode(object):
    def __init__(self, world, sensors):
        self.world = world
        self.sensors = sensors
        self.frame = None
        self._queues = []
        #self._settings = None
        self.first_time = True

    def __enter__(self):
        def make_queue(register_event):
            q = queue.Queue()
            register_event(q.put)
            self._queues.append(q)

        make_queue(self.world.on_tick)
        for sensor in self.sensors:
            make_queue(sensor.listen)
        return self

    def tick(self, timeout):
        self.frame = self.world.tick()
        
        #print("Before: " + str(self._queues[1].qsize()))
        #time.sleep(5.0)
        #print("After: " + str(self._queues[1].qsize()))
        #data = self._retrieve_data(self._queues[1], timeout)

        data = [self._retrieve_data(q, timeout) for q in self._queues]
        #print(data)
        assert all(x.frame == self.frame for x in data)
        return data

    def __exit__(self, *args, **kwargs):
        print("Got exit function!")
        return
        #self.world.apply_settings(self._settings)

    def _retrieve_data(self, sensor_queue, timeout):
        while True:
            data = sensor_queue.get(timeout=timeout)
            if data.frame == self.frame:
                return data
            else:
                print("frame mismatch")
                print(data.frame)
                print(self.frame)


def setupTrafficManager(client):
    print("Settting up traffic manager...")
    tm = client.get_trafficmanager(8000)
    tm.set_synchronous_mode(True)

def setupWorld(world):
    print("Settting up world...")
    settings = world.get_settings()
    settings.fixed_delta_seconds = SimulationParams.delta_seconds
    settings.synchronous_mode = True
    world.set_pedestrians_cross_factor(0.0)
    world.apply_settings(settings)

#This will create the whole file system structure. It will create a separate folder for each sensor
def createOutputDirectories(data):
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
    PHASE = SimulationParams.town_map + "_" + dt_string
    SimulationParams.data_output_subfolder = os.path.join(SimulationParams.data_output_root_folder, PHASE)

    output_sensor_folders = [ os.path.join(SimulationParams.data_output_subfolder, data['sensors'][i]['type']) for i in range(len(data['sensors'])) ]
    try:
        os.mkdir(SimulationParams.data_output_root_folder)
    except OSError:
        print("Folder " + SimulationParams.data_output_root_folder + " already exists!")
    os.mkdir(SimulationParams.data_output_subfolder)
    for folder in output_sensor_folders:
        try:
            os.mkdir(folder)
        except OSError:
            print("Creation of " + folder + " failed")
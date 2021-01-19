import os

def saveAllSensors(out_root_folder, sensor_data, sensor_types):

    #TODO have it find the snapshot object dynamically instead of using the hardcoded 0 index
    saveSnapshot(out_root_folder, sensor_data[0])
    sensor_data.pop(0)

    for i in range(len(sensor_data)):
        sensor_name = sensor_types[i]
        if(sensor_name == 'sensor.camera.rgb'):
            saveImage(sensor_data[i], os.path.join(out_root_folder, sensor_name))
        if(sensor_name == 'sensor.lidar.ray_cast' or sensor_name == 'sensor.lidar.ray_cast_semantic'):
            saveLidar(sensor_data[i], os.path.join(out_root_folder, sensor_name))
    return

def saveSnapshot(output, filepath):
    return

def saveSteeringAngle(value, filepath):
    with open(filepath + "/steering_norm.txt", 'a') as fp:
        fp.writelines(str(value) + ", ")
    with open(filepath + "/steering_true.txt", 'a') as fp:
        fp.writelines(str(70*value) + ", ")

def saveGnss(output, filepath):
    return

def saveImu(output, filepath):
    return

def saveLidar(output, filepath):
    output.save_to_disk(filepath + '/%05d'%output.frame)
    with open(filepath + "/lidar_metadata.txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")


def saveImage(output, filepath):
    output.save_to_disk(filepath + '/%05d'%output.frame)
    with open(filepath + "/camera_metadata.txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")
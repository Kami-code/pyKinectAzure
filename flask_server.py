import subprocess
import signal
import time

from flask import Flask, request
import json
import os
import requests
import sys
import cv2

sys.path.insert(1, './')
import pykinect_azure as pykinect
import numpy as np
import time
app = Flask(__name__)
# CORS(app, supports_credentials=True)

procs = list()
device_list = list()


@app.route('/Pod/<string:instance_name>/<string:behavior>', methods=['POST'])
def post_pod(instance_name: str, behavior: str):
    if behavior == 'create':
        json_data = request.json
        config: dict = json.loads(json_data)
        put(instance_name, config)
        config['behavior'] = 'create'
    elif behavior == 'update':  # update pods information such as ip
        json_data = request.json
        config: dict = json.loads(json_data)
        put(instance_name, config)
        return 'success', 200
    elif behavior == 'remove':
        config = get(instance_name)
        config['status'] = 'Removed'
        put(instance_name, config)
        config['behavior'] = 'remove'
    elif behavior == 'execute':
        config = get(instance_name)
        json_data = request.json
        upload_cmd: dict = json.loads(json_data)
        # if config.get('cmd') is not None and config['cmd'] != upload_cmd['cmd']:
        config['behavior'] = 'execute'
        config['cmd'] = upload_cmd['cmd']
    elif behavior == 'delete':
        pods_list: list = get('pods_list')
        index = -1
        for i, pod_instance_name in enumerate(pods_list):
            if pod_instance_name == instance_name:
                index = i
        pods_list.pop(index)
        delete_key(instance_name)
        put('pods_list', pods_list)
        return "success", 200
    else:
        return json.dumps(dict()), 404
    # todo: post pod information to related node

    worker_url = None
    pods_list = get('pods_list')
    for pod_instance_name in pods_list:
        if instance_name == pod_instance_name:
            pod_config = get(pod_instance_name)
            if pod_config.get('node') is not None:
                node_instance_name = pod_config['node']
                node_config = get(node_instance_name)
                worker_url = node_config['url']
    if worker_url is not None:  # only scheduler successfully will have a worker_url
        r = requests.post(url=worker_url + "/Pod", json=json.dumps(config))
    # broadcast_message('Pod', config.__str__())
    return json.dumps(config), 200


@app.route('/start', methods=['GET'])
def start_record():
    for process in procs:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    for i in range(3):
        process = subprocess.Popen(
            f"C:\\Program Files\\Azure Kinect SDK v1.4.1\\tools\\k4arecorder.exe --device {i + 1} --external-sync Subordinate output{i + 1}.mkv",)
        procs.append(process)
    process = subprocess.Popen(
        f"C:\\Program Files\\Azure Kinect SDK v1.4.1\\tools\\k4arecorder.exe --device 0 --external-sync Master output0.mkv",)
    procs.append(process)
    procs.reverse()
    return json.dumps({"Started": "Started"}), 200


@app.route('/stop', methods=['GET'])
def stop_record():
    for process in procs:
        process.send_signal(signal.CTRL_C_EVENT)
    return json.dumps({"Stopped": "Stopped"}), 200


@app.route('/shot/<int:number>', methods=['GET'])
def single_shot(number: int):
    serial_map = {0:"000673513312", 1:"000700713312", 2:"000760113312"}


    device_list = list()
    # Modify camera configuration
    device_config = pykinect.default_configuration
    device_config.wired_sync_mode = pykinect.K4A_WIRED_SYNC_MODE_STANDALONE
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
    device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
    device: pykinect.Device = pykinect.start_device(device_index=0, config=device_config)
    print(device)
    device_list.append(device)
    device_config = pykinect.default_configuration
    device_config.wired_sync_mode = pykinect.K4A_WIRED_SYNC_MODE_STANDALONE
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
    device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED

    current_frame = list()
    current_depth_frame = list()
    for i in range(1, 3, 1):
        device = pykinect.start_device(device_index=i, config=device_config)
        device_list.append(device)
        print(device)
    # device_list.reverse()
    while True:
        try:
            current_frame.clear()
            current_depth_frame.clear()
            for i, device in enumerate(device_list):
                # Get capture
                capture = device.update()
                # Get the color image from the capture
                # ret, color_image = capture.get_color_image()

                ret_color, color_image = capture.get_color_image()

                # Get the colored depth
                ret_depth, transformed_colored_depth_image = capture.get_transformed_depth_image()
                if (not ret_color) or (not ret_depth):
                    continue
                # print(color_image)
                # print(transformed_colored_depth_image)
                current_frame.append(color_image)
                current_depth_frame.append(transformed_colored_depth_image)
                # print(f"shape = {color_image.shape}")
            if len(current_frame) == 3:
                break
        except Exception as e:
            print(e)
    for i in range(3):
        if not os.path.exists(f"./save/{serial_map[i]}"):
            os.mkdir(f"./save/{serial_map[i]}")
            os.mkdir(f"./save/{serial_map[i]}/color")
        if not os.path.exists(f"./save/{serial_map[i]}/depth"):
            os.mkdir(f"./save/{serial_map[i]}/depth")
        cv2.imwrite(f"./save/{serial_map[i]}/color/{number}.png", current_frame[i])
        np.save(f"./save/{serial_map[i]}/depth/{number}.npy", current_depth_frame[i])
    # im12 = np.concatenate([current_frame[0], current_frame[1]], axis=1)
    # im34 = np.concatenate([current_frame[2], current_frame[3]], axis=1)
    # im_all = np.concatenate([im12, im34], axis=0)
    # scale = 3
    # im_all = cv2.resize(im_all, (384 * scale, 216 * scale))
    # # Plot the image
    # # cv2.imshow(f"Color Image", im_all)
    # cv2.imwrite("./current.png", im_all)
    for device in device_list:
        device.close()
    return json.dumps({"Done": "Done"}), 200


@app.route('/list', methods=['GET'])
def get_function():
    return_dict = dict()
    process = subprocess.Popen(
        f"C:\\Program Files\\Azure Kinect SDK v1.4.1\\tools\\k4arecorder.exe --list",
        stdout=subprocess.PIPE
    )
    output = process.communicate()[0].decode("utf-8")
    output = output.split('\r\n')[:-1]
    for device_string in output:
        try:
            device = device_string.split('\t')
            result = dict()
            for device_property in device:
                device_property_list = device_property.split(':')
                result[device_property_list[0]] = device_property_list[1]
            return_dict[result['Index']] = result
        except Exception as e:
            print(e)
    return json.dumps(return_dict), 200


def main():
    app.run(port=5050)


if __name__ == '__main__':
    pykinect.initialize_libraries()
    main()

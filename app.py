# -*- coding: utf-8 -*-

"""
    Tooloop Control
    ~~~~~~~~~~~~~~~~~~~~~~~
    Control Center for Tooloop OS
    :copyright: (c) 2022 by Daniel Stock.
    :license: MIT, see LICENSE for more details.
"""

from flask import Flask, jsonify, render_template, request, after_this_request, abort, send_from_directory, make_response, Response
from jinja2 import ChoiceLoader, FileSystemLoader

# import augeas
import time
import json
import os

from sys import platform
from pprint import pprint
from subprocess import call
from pathlib import Path


from controllers.system_controller import System
from controllers.presentation_controller import Presentation
from controllers.appcenter_controller import AppCenter, PackageJSONEncoder
from controllers.services_controller import Services
from controllers.screenshot_controller import Screenshots
from controllers.network_discovery_controller import NetworkDiscovery
from utils.time_utils import *
from utils.exceptions import *


# ------------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_pyfile('data/config.cfg')
os.environ['FLASK_ENV'] = app.config['ENVIRONMENT']

system = System(app)
presentation = Presentation()
appcenter = AppCenter(presentation, app)
services = Services(app)
screenshots = Screenshots()
network_discovery = NetworkDiscovery()


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route('/')
@app.route("/dashboard")
def index():
    return render_template('dashboard.html',
                           environment=os.environ['FLASK_ENV'],
                           page='dashboard',
                           hostname=system.get_hostname(),
                           ip_address=system.get_ip(),
                           servers=network_discovery.get_servers(),
                           display_state=system.get_display_state(),
                           audio_mute=system.get_audio_mute(),
                           audio_volume=system.get_audio_volume(),
                           uptime=time_to_ISO_string(system.get_uptime()),
                           screenshot_service_running=services.is_screenshot_service_running(),
                           )


@app.route("/appcenter")
def render_appcenter():
    return render_template('appcenter.html',
                           page='appcenter',
                           installed_presentation=appcenter.get_installed_presentation(),
                           available_packages=appcenter.get_available_packages(),
                           )


@app.route("/appcenter/<string:package>")
def render_package_detail(package):
    return render_template('package-detail.html',
                           page='appcenter',
                           package=appcenter.get_package(package),
                           installed_presentation=appcenter.get_installed_presentation()
                           )


@app.route("/services")
def render_services():
    return render_template('services.html',
                           page='services',
                           ip_address=system.get_ip(),
                           services=services.get_status(),
                           )


@app.route("/system")
def render_system():
    return render_template('system.html',
                           page='system',
                           os_version="22.04",
                           hostname=system.get_hostname(),
                           ip_address=system.get_ip(),
                           uptime=time_to_ISO_string(system.get_uptime()),
                           timezone=system.get_timezone(),
                           ssh_running=services.is_ssh_running(),
                           vnc_running=services.is_vnc_running(),
                           runtime_schedule=system.get_runtime_schedule(),
                           )


# ------------------------------------------------------------------------------
# ADDITIONAL RESOURCE FOLDERS
# ------------------------------------------------------------------------------

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    return send_from_directory('/assets/screenshots/', filename)


@app.route('/app/<path:filename>')
def serve_installed_app(filename):
    return send_from_directory('installed_app/', filename)


@app.route('/appcenter/media/<path:filename>')
def serve_package_media(filename):
    return send_from_directory('/assets/packages/media', filename)


# ------------------------------------------------------------------------------
# RESTFUL API
# ------------------------------------------------------------------------------

@app.route('/tooloop/api/v1.0/reload', methods=['GET'])
def reload():
    # touching data/reload will trigger the auto reloader
    # TODO: change to proper reloading as this only works in development mode
    Path(os.path.join(app.root_path, 'data', 'reload')).touch()
    return jsonify({'message': 'Control Center reloaded'})


# System

@app.route('/tooloop/api/v1.0/system', methods=['GET'])
def get_system():
    return jsonify(system.to_dict())


@app.route('/tooloop/api/v1.0/system/hostname', methods=['GET'])
def get_hostname():
    try:
        return jsonify({'hostname': system.get_hostname()})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/hostname', methods=['PUT'])
def set_hostname():
    if not request.get_json() or not 'hostname' in request.get_json():
        abort(400)
    try:
        system.set_hostname(request.get_json()['hostname'])
        return jsonify({'hostname': system.get_hostname()})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/usage', methods=['GET'])
def get_usage():
    return jsonify({
        'hd': system.get_hd(),
        'cpu': system.get_cpu(),
        'gpu': system.get_gpu(),
        'memory': system.get_memory()
    })


@app.route('/tooloop/api/v1.0/system/uptime', methods=['GET'])
def get_uptime():
    return jsonify({'uptime': time_to_ISO_string(system.get_uptime())})


@app.route('/tooloop/api/v1.0/system/hd', methods=['GET'])
def get_hd():
    return jsonify(system.get_hd())


@app.route('/tooloop/api/v1.0/system/cpu', methods=['GET'])
def get_cpu():
    return jsonify(system.get_cpu())


@app.route('/tooloop/api/v1.0/system/gpu', methods=['GET'])
def get_gpu():
    return jsonify(system.get_gpu())


@app.route('/tooloop/api/v1.0/system/memory', methods=['GET'])
def get_memory():
    return jsonify(system.get_memory())


@app.route('/tooloop/api/v1.0/system/reboot', methods=['GET'])
def reboot():
    try:
        system.reboot()
        return jsonify({'message': 'Rebooting'})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/poweroff', methods=['GET'])
def poweroff():
    try:
        system.poweroff()
        return jsonify({'message': 'Powering Off'})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/password', methods=['PUT'])
def set_password():
    if not request.get_json() or not 'oldPassword' in request.get_json() or not 'newPassword' in request.get_json():
        abort(400)
    try:
        message = system.set_password(
            request.get_json()['oldPassword'], request.get_json()['newPassword'])
        return jsonify({'message': message})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/audiovolume', methods=['GET'])
def get_audio_volume():
    return jsonify({'volume': system.get_audio_volume()})


@app.route('/tooloop/api/v1.0/system/audiovolume', methods=['PUT'])
def set_audio_volume():
    if not request.get_json() or not 'volume' in request.get_json():
        abort(400)
    try:
        volume = int(float(request.get_json()['volume']))
        system.set_audio_volume(volume)
        return jsonify({'volume': str(volume)})
    except Exception as e:
        raise e


@app.route('/tooloop/api/v1.0/system/audiomute', methods=['GET'])
def get_audio_mute():
    return jsonify({'mute': system.get_audio_mute()})


@app.route('/tooloop/api/v1.0/system/audiomute', methods=['PUT'])
def set_audio_mute():
    if not request.get_json() or not 'mute' in request.get_json():
        abort(400)
    try:
        mute = request.get_json()['mute']
        system.set_audio_mute(mute)
        return jsonify({'mute': mute})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/displaystate', methods=['GET'])
def get_display_state():
    try:
        state = system.get_display_state()
        return jsonify({'state': state})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/displaystate', methods=['PUT'])
def set_display_state():
    if not request.get_json() or not 'state' in request.get_json():
        abort(400)
    try:
        system.set_display_state(request.get_json()['state'])
        state = system.get_display_state()
        return jsonify({'state': state})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/runtimeschedule', methods=['GET'])
def get_runtime_schedule():
    try:
        return jsonify(system.get_runtime_schedule())
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/runtimeschedule', methods=['PUT'])
def set_runtime_schedule():
    if not request.get_json():
        abort(400)
    try:
        system.set_runtime_schedule(request.get_json())
        return jsonify(system.get_runtime_schedule())
    except Exception as e:
        abort(500, e)


# presentation

@app.route('/tooloop/api/v1.0/presentation/start', methods=['GET'])
def start_presentation():
    return_code = presentation.start()
    try:
        return jsonify({'start': str(return_code)})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/presentation/stop', methods=['GET'])
def stop_presentation():
    return_code = presentation.stop()
    try:
        return jsonify({'stop': str(return_code)})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/presentation/reset', methods=['GET'])
def reset_presentation():
    try:
        return_code = presentation.reset()
        return jsonify({'reset': str(return_code)})
    except Exception as e:
        abort(500, e)


# screenshots

@app.route('/tooloop/api/v1.0/screenshot/latest', methods=['GET'])
def get_latest_screenshot():
    return jsonify(screenshots.get_latest_screenshot())


@app.route('/tooloop/api/v1.0/screenshot/<int:index>', methods=['GET'])
def get_screenshot(index):
    return jsonify(screenshots.get_screenshot(index))


@app.route('/tooloop/api/v1.0/screenshot/date/<string:date>', methods=['GET'])
def get_screenshot_at_date(date):
    return jsonify(screenshots.get_screenshot_at_date(date))


@app.route('/tooloop/api/v1.0/screenshot/grab', methods=['GET'])
def grab_screenshot():
    try:
        return jsonify(screenshots.grab_screenshot())
    except Exception as e:
        abort(500, e)


# services

@app.route('/tooloop/api/v1.0/services', methods=['GET'])
def get_services_status():
    return jsonify(services.get_status())


@app.route('/tooloop/api/v1.0/services/vnc', methods=['GET'])
def vnc_status():
    return jsonify({'vnc': services.is_vnc_running()})


@app.route('/tooloop/api/v1.0/services/vnc', methods=['PUT'])
def set_vnc():
    if not request.get_json() or not 'vnc' in request.get_json():
        abort(400)
    try:
        state = request.get_json()['vnc']
        if state == True:
            services.enable_vnc()
        else:
            services.disable_vnc()
        return jsonify({'vnc': services.is_vnc_running()})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/services/ssh', methods=['GET'])
def ssh_status():
    return jsonify({'ssh': services.is_ssh_running()})


@app.route('/tooloop/api/v1.0/services/ssh', methods=['PUT'])
def set_ssh():
    if not request.get_json() or not 'ssh' in request.get_json():
        abort(400)
    try:
        state = request.get_json()['ssh']
        if state == True:
            services.enable_ssh()
        else:
            services.disable_ssh()
        return jsonify({'ssh': services.is_ssh_running()})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/services/controlcenter', methods=['GET'])
def control_center_status():
    return jsonify({'control_center': services.is_control_center_running()})


@app.route('/tooloop/api/v1.0/services/controlcenter', methods=['PUT'])
def set_control_center():
    if not request.get_json() or not 'control_center' in request.get_json():
        abort(400)
    try:
        state = request.get_json()['control_center']
        if state == True:
            services.enable_control_center()
        else:
            services.disable_control_center()
        return jsonify({'control_center': services.is_control_center_running()})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/services/screenshots', methods=['GET'])
def screenshot_service_status():
    return jsonify({'screenshot_service': services.is_screenshot_service_running()})


@app.route('/tooloop/api/v1.0/services/screenshots', methods=['PUT'])
def set_screenshot_service():
    if not request.get_json() or not 'screenshot_service' in request.get_json():
        abort(400)
    try:
        state = request.get_json()['screenshot_service']
        if state == True:
            services.enable_screenshot_service()
        else:
            services.disable_screenshot_service()
        return jsonify({'screenshot_service': services.is_screenshot_service_running()})
    except Exception as e:
        abort(500, e)


# appcenter

@app.route('/tooloop/api/v1.0/appcenter/installed', methods=['GET'])
def get_installed_app():
    return jsonify(appcenter.get_installed_presentation())


@app.route('/tooloop/api/v1.0/appcenter/available', methods=['GET'])
def get_available_packages():
    return jsonify(appcenter.packages)


@app.route('/tooloop/api/v1.0/appcenter/refresh', methods=['GET'])
def update_packages():
    appcenter.update_packages()
    return appcenter.packages


@app.route('/tooloop/api/v1.0/appcenter/install/<string:name>', methods=['GET'])
def install_package(name):
    try:
        appcenter.install(name)
        return jsonify({'message': name+' installed successfully'})
    except InvalidUsage as e:
        return make_response(jsonify({'message': e.message}), e.status_code)
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/appcenter/uninstall/<string:name>', methods=['GET'])
def uninstall_package(name):
    try:
        appcenter.uninstall(name)
        return jsonify({'message': name+' uninstalled successfully'})
    except InvalidUsage as e:
        return make_response(jsonify({'message': e.message}), e.status_code)
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/appcenter/package/<string:name>', methods=['GET'])
def get_package(name):
    pkg = appcenter.get_package(name)
    return jsonify(pkg)


@app.route('/tooloop/api/v1.0/appcenter/progress')
def appcenter_progress():
    def progress():
        progress = appcenter.get_progress()
        while True:
            yield 'data: '+json.dumps(progress)+'\n\n'
            if progress['status'] != 'ok':
                break
            time.sleep(0.1)

    return Response(progress(), mimetype='text/event-stream')


# network discovery

@app.route('/tooloop/api/v1.0/networkdiscovery/servers', methods=['GET'])
def get_servers():
    return jsonify(network_discovery.get_servers())


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app.json_encoder = PackageJSONEncoder
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        extra_files=[os.path.join(app.root_path, 'data', 'reload')]
    )

#!/usr/bin/env python3

import click
import os
import re
import time
import datetime

""" config dictionary
key       type        default
-----------------------------
signal    int         9
log       boolean     true 
jetty     boolean     false
...
"""
config = {}


@click.group()
@click.option("--log/--no-log", "-l/-n", is_flag=True, default=True, help="Does show log? default true")
@click.option("--signal", "-s", default=9, type=int,
              help="Send the SIGNAL to the process of server,Default use SIGKILL(9)")
@click.option("--jetty", "-j", is_flag=True, default=False, help="Is jetty mode? default False")
def ctrl(signal, log, jetty):
    """a simple tools to control java server"""
    config["signal"] = signal
    config["log"] = log
    config["jetty"] = jetty


@ctrl.command("start")
@click.argument("file")
def start(file):
    """start a server use the spring-boot project file or jetty path"""
    if not config["jetty"]:
        if not os.path.isfile(file):
            click.echo("Please give the filename")
            return
        abspath = os.path.abspath(file)
        filename = os.path.basename(abspath)
        cwd = os.path.dirname(abspath)
        click.echo("Start the project:%s" % abspath)
        start_cmd = "cd %s && nohup java -jar %s --spring.profiles.active=prod >/dev/null 2>&1 &" % (cwd, filename)
    else:
        if not os.path.isdir(file):
            click.echo("Please give a path")
            return
        cwd = file
        start_cmd = "cd %s && nohup java -jar ../start.jar >/dev/null 2>&1 &" % file
    os.system(start_cmd)
    print(start_cmd)
    print_log(cwd)


@ctrl.command("restart")
@click.argument("port", type=int)
def restart(port):
    """restart the server which use the PORT"""
    pid = get_pid_by_port(port)
    click.echo("Restart the server which use the port:%s [pid:%s]" % (port, pid))
    if pid:
        cwd = get_cwd_by_pid(pid)
        cmd = get_start_cmd_by_pid(pid)
        if cwd and cmd:
            kill_by_pid(pid)
            time.sleep(1)
            os.system("cd %s && %s" % (cwd, cmd))
            print_log(cwd)


@ctrl.command("stop")
@click.argument("port", type=int)
def stop(port):
    """stop the server which use the PORT"""
    pid = get_pid_by_port(port)
    click.echo("Stop the server which use the port:%s [pid:%s]" % (port, pid))
    kill_by_pid(pid)


@ctrl.command("log")
@click.argument("port", type=int)
def show_log(port):
    """print the log file use the PORT"""
    pid = get_pid_by_port(port)
    if pid:
        cwd = get_cwd_by_pid(pid)
        if cwd:
            print_log(cwd)


def get_pid_by_port(port):
    find_port_cmd = "lsof -i:" + str(port) + "|grep java|grep LISTEN"
    ret = os.popen(find_port_cmd)
    used_port_line = ret.readline()
    if used_port_line:
        splitted = re.split("\s+", used_port_line)
        return splitted[1]
    else:
        click.echo("The port:%s is not in use" % port)


def get_cwd_by_pid(pid):
    get_cwd_cmd = "ls -l /proc/%d | grep 'cwd ->' | sed 's/.*cwd -> //'" % int(pid)
    ret = os.popen(get_cwd_cmd)
    cwd = ret.readline().strip()
    if cwd:
        return cwd
    else:
        click.echo("No process with id:%s is on use" % pid)


def get_start_cmd_by_pid(pid):
    cmd = "ps -ef|grep %d |grep -v grep" % int(pid)
    ret = os.popen(cmd)
    cmd_line = ret.readline().strip()
    if cmd_line:
        splited = re.split("\s+", cmd_line, 7)
        cmd = splited[7]
        return "nohup %s >/dev/null 2>&1 &" % cmd
    else:
        click.echo("Can not get the start cmd for pid:%s" % pid)


def kill_by_pid(pid):
    kill_cmd = "kill -%s %s" % (config["signal"], pid)
    click.echo("The pid:%d will be stop" % int(pid))
    os.system(kill_cmd)


def print_log(cwd):
    if cwd[-1] != os.path.sep:
        cwd += os.path.sep
    if config["log"]:
        if not config["jetty"]:
            file_name = cwd.split(os.path.sep)[-2]
        else:
            now = datetime.datetime.now()
            hour = now.hour
            if hour < 8:
                now = now - datetime.timedelta(days=1)
            file_name = "logs/" + now.strftime("%Y_%m_%d.stderrout")
        path_file = cwd + file_name + '.log'
        os.system("tail -F %s" % path_file)


if __name__ == "__main__":
    ctrl()
    click.echo("Finished")

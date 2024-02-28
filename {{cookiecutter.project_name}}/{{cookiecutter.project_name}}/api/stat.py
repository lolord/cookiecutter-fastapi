import functools
import json
import os
import platform
from typing import Any, Dict, List

import psutil
from db.backend import redis_db
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field
from schemas import Pagination, PaginationQuery, PaginationResp

router = APIRouter(prefix="/server-stat", tags=["SERVER STAT"])

# https://www.liaoxuefeng.com/wiki/1016959663602400/1017805733037760


class CPU(BaseModel):
    cpu: float
    cpus: list[float]
    at: int


@router.get("/cpu", summary="获取cpu占用率", response_model=List[CPU])
async def get_cpu(
    limit: int = Query(
        1, description="查询 [1, 3, 5, 10, 15, 30, 60] 分钟内的cpu使用率"
    ),
):
    return [json.loads(i) for i in redis_db.lrange("sys_cpu_dynamic", 0, limit * 60)]


@functools.lru_cache(1)
def get_cpu_type():
    try:
        with open("/proc/cpuinfo") as f:  # 获取cpu型号
            for line in f:
                if line.strip():
                    if line.rstrip("\n").startswith("model name"):
                        cpu_name = line.rstrip("\n").split(":")[1]
                        return cpu_name.split()[0]
    except IOError:
        return "No permission"


@functools.lru_cache(1)
def system_parameter():
    cpu_thread = psutil.cpu_count()  # CPU逻辑数量
    cpu_core = psutil.cpu_count(logical=False)  # CPU物理核心
    host_name = platform.node()  # 电脑名称
    psutil.process_iter()
    sysname, nodename, release, version, machine = os.uname()  # type: ignore
    return {
        "cpu_type": get_cpu_type(),
        "cpu_thread": cpu_thread,
        "cpu_core": cpu_core,
        "host_name": host_name,
        "sysname": sysname,
        "nodename": nodename,
        "release": release,
        "version": version,
        "machine": machine,  # 获取操作系统架构
    }


class SystemParameter(BaseModel):
    cpu_type: str = Field(..., description="cpu型号")
    cpu_core: int = Field(..., description="cpu核数")
    cpu_thread: int = Field(..., description="CPU逻辑数量")
    host_name: str = Field(..., description="电脑名称")
    sysname: str = Field(..., description="版本详细信息")
    nodename: str = Field(..., description="操作系统名称")
    release: str = Field(..., description="操作系统版本")
    version: str = Field(..., description="版本详细信息")
    machine: str = Field(..., description="操作系统架构")


@router.get("/system-parameter", summary="获取系统参数", response_model=SystemParameter)
async def get_system_parameter():
    return system_parameter()


class Memory(BaseModel):
    total: int = Field(..., description="系统内存总数")
    used: int = Field(..., description="内存已使用")
    free: int = Field(..., description="内存空闲大小")
    per: float = Field(..., description="内存使用率")


@router.get("/memory", summary="获取内存占用率", response_model=List[Memory])
async def get_memory(
    limit: int = Query(
        1, description="查询 [1, 3, 5, 10, 15, 30, 60] 分钟内的cpu使用率"
    ),
):
    return [json.loads(i) for i in redis_db.lrange("sys_mem_dynamic", 0, limit * 12)]


class DiskUsage(BaseModel):
    total: int = Field(..., description="系统内存总数")
    used: int = Field(..., description="磁盘已使用")
    free: int = Field(..., description="磁盘空闲大小")
    percent: float = Field(..., description="磁盘使用率")


@router.get("/disk-usage", summary="磁盘使用情况", response_model=DiskUsage)
async def get_disk_usage():
    return psutil.disk_usage("/")._asdict()


class DiskIO(BaseModel):
    read_count: int = Field(..., description="磁盘读入次数")
    write_count: int = Field(..., description="磁盘写入次数")
    read_bytes: int = Field(..., description="磁盘读入大小")
    write_bytes: int = Field(..., description="磁盘写入大小")
    read_time: int = Field(..., description="磁盘读入时间")
    write_time: int = Field(..., description="磁盘写入时间")


@router.get("/disk-io", summary="磁盘io", response_model=DiskIO)
async def get_disk_io():
    return psutil.disk_io_counters()._asdict()  # type: ignore


class Process(BaseModel):
    pid: int = Field(..., description="进程ID")
    ppid: int = Field(..., description="父进程ID")
    name: str = Field(None, description="进程名称")
    exe: str = Field(None, description="进程exe路径")
    cwd: str = Field(None, description="进程工作目录")
    cmdline: List[str] = Field(None, description="进程启动的命令行")
    status: str = Field(..., description="进程状态")
    username: str = Field(None, description="进程用户名")
    create_time: float = Field(..., description="进程创建时间")
    terminal: str = Field(None, description="进程终端")


@router.get("/process", summary="进程列表", response_model=PaginationResp[Process])
async def get_process(query: PaginationQuery = Depends()):
    start = (query.page - 1) * query.page_size
    end = start + query.page_size
    pids = psutil.pids()
    data = []
    for pid in pids[start:end]:
        p = psutil.Process(pid)
        data.append(
            {
                "pid": pid,
                "ppid": p.ppid(),  # 父进程ID
                "name": p.name(),
                "exe": p.exe(),  # 进程exe路径
                "cwd": p.cwd(),  # 进程工作目录
                "cmdline": p.cmdline(),  # 进程启动的命令行
                "status": p.status(),  # 进程状态
                "username": p.username(),  # 进程用户名
                "create_time": p.create_time(),  # 进程创建时间
                "terminal": p.terminal(),  # 进程终端 # type: ignore
            }
        )
    total = len(pids)
    pagination = Pagination(
        total=total, page=query.page, page_size=query.page_size, total_count=total
    )
    return PaginationResp(data=data, pagination=pagination)


@router.get("/process/{pid}", summary="进程详情", response_model=Dict[str, Any])
async def get_process_detail(pid: int = Path(...)):
    return psutil.Process(pid).as_dict()

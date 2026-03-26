import flet as ft
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
import threading
import asyncio

# Mock VM data model
class MockVM:
    def __init__(self, id: int, name: str, status: str = "running", 
                 cpu: float = 0.0, memory: float = 0.0, disk: float = 0.0):
        self.id = id
        self.name = name
        self.status = status
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.ip = f"192.168.1.{random.randint(10, 250)}"
        self.created = datetime.now()
        self.os_type = random.choice(["Ubuntu 22.04", "CentOS 8", "Windows Server 2022", "Debian 11"])
        self.vcpu = random.randint(1, 8)
        self.ram = f"{random.choice([2, 4, 8, 16])}GB"
        self.storage = f"{random.choice([50, 100, 200, 500])}GB"

# Mock backend service
class MockVMBackend:
    def __init__(self):
        self.vms = [
            MockVM(1, "Web-Server-01", "running", 45.2, 67.8, 32.1),
            MockVM(2, "DB-Server-01", "running", 23.1, 89.2, 45.6),
            MockVM(3, "Test-VM-01", "stopped", 0.0, 0.0, 12.3),
            MockVM(4, "Backup-Server", "running", 12.5, 34.6, 78.9),
            MockVM(5, "Dev-Environment", "paused", 0.0, 12.3, 23.4),
        ]
        self.next_id = 6
        
    def get_all_vms(self) -> List[MockVM]:
        return self.vms
    
    def create_vm(self, name: str, os_type: str, vcpu: int, ram: str, storage: str) -> MockVM:
        vm = MockVM(
            id=self.next_id,
            name=name,
            status="creating",
            cpu=0.0,
            memory=0.0,
            disk=0.0
        )
        vm.os_type = os_type
        vm.vcpu = vcpu
        vm.ram = ram
        vm.storage = storage
        self.vms.append(vm)
        self.next_id += 1
        
        # Simulate creation process
        def simulate_creation():
            time.sleep(2)
            vm.status = "running"
            vm.cpu = random.uniform(5, 25)
            vm.memory = random.uniform(30, 70)
            vm.disk = random.uniform(10, 40)
        
        threading.Thread(target=simulate_creation, daemon=True).start()
        return vm
    
    def delete_vm(self, vm_id: int) -> bool:
        for i, vm in enumerate(self.vms):
            if vm.id == vm_id:
                del self.vms[i]
                return True
        return False
    
    def change_vm_status(self, vm_id: int, action: str) -> bool:
        for vm in self.vms:
            if vm.id == vm_id:
                old_status = vm.status
                if action == "start":
                    vm.status = "starting"
                elif action == "stop":
                    vm.status = "stopping"
                elif action == "restart":
                    vm.status = "restarting"
                elif action == "pause":
                    vm.status = "pausing"
                
                # Simulate status change
                def simulate_status_change():
                    time.sleep(1)
                    if action == "start":
                        vm.status = "running"
                        vm.cpu = random.uniform(10, 50)
                        vm.memory = random.uniform(40, 90)
                    elif action == "stop":
                        vm.status = "stopped"
                        vm.cpu = 0.0
                        vm.memory = 0.0
                    elif action == "restart":
                        vm.status = "running"
                        vm.cpu = random.uniform(10, 50)
                        vm.memory = random.uniform(40, 90)
                    elif action == "pause":
                        vm.status = "paused"
                        vm.cpu = 0.0
                
                threading.Thread(target=simulate_status_change, daemon=True).start()
                return True
        return False
    
    def update_metrics(self):
        """Simulate changing VM metrics"""
        for vm in self.vms:
            if vm.status == "running":
                vm.cpu = min(100, max(0, vm.cpu + random.uniform(-5, 5)))
                vm.memory = min(100, max(0, vm.memory + random.uniform(-3, 3)))
                vm.disk = min(100, max(0, vm.disk + random.uniform(-1, 1)))

def main(page: ft.Page):
    page.title = "VM Management Platform"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.padding = 20
    
    # Initialize backend
    backend = MockVMBackend()
    
    # Create title
    title = ft.Text(
        "Virtual Machine Management Platform",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_700
    )
    
    # Status bar
    status_bar = ft.Text(
        "Ready",
        size=12,
        color=ft.Colors.GREY_600
    )
    
    # Dashboard components
    total_vms = ft.Text("0", size=36, weight=ft.FontWeight.BOLD)
    running_vms = ft.Text("0", size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    stopped_vms = ft.Text("0", size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    activity_log = ft.Column(
        spacing=5,
        height=200,
        scroll=ft.ScrollMode.AUTO
    )
    
    # VM List components
    vm_list_view = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
    
    # Create VM components
    vm_name = ft.TextField(
        label="VM Name",
        hint_text="Enter VM name",
        prefix_icon=ft.Icons.COMPUTER,
        expand=True,
    )
    
    os_type = ft.Dropdown(
        label="Operating System",
        hint_text="Select OS",
        options=[
            ft.dropdown.Option("Ubuntu 22.04"),
            ft.dropdown.Option("CentOS 8"),
            ft.dropdown.Option("Windows Server 2022"),
            ft.dropdown.Option("Debian 11"),
            ft.dropdown.Option("AlmaLinux 9"),
        ],
        value="Ubuntu 22.04",
        expand=True,
    )
    
    vcpu_count = ft.Dropdown(
        label="vCPUs",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 9)],
        value="2",
        expand=True,
    )
    
    ram_size = ft.Dropdown(
        label="RAM",
        options=[ft.dropdown.Option(f"{i}GB") for i in [2, 4, 8, 16, 32]],
        value="4GB",
        expand=True,
    )
    
    storage_size = ft.Dropdown(
        label="Storage",
        options=[ft.dropdown.Option(f"{i}GB") for i in [50, 100, 200, 500, 1000]],
        value="100GB",
        expand=True,
    )
    
    creation_status = ft.Text("", color=ft.Colors.GREEN)
    
    # Monitoring components
    cpu_line_chart = ft.LineChart(
        border=ft.border.all(1, ft.Colors.GREY_400),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_900),
        expand=True,
        height=250,
    )

    mem_line_chart = ft.LineChart(
        border=ft.border.all(1, ft.Colors.GREY_400),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_900),
        expand=True,
        height=250,
    )

    disk_line_chart = ft.LineChart(
        border=ft.border.all(1, ft.Colors.GREY_400),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_900),
        expand=True,
        height=250,
    )
    
    metrics_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("VM Name")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("CPU %")),
            ft.DataColumn(ft.Text("Memory %")),
            ft.DataColumn(ft.Text("Disk %")),
        ],
        rows=[],
    )

    history = {}   # { vm_id: { "cpu": [], "mem": [], "disk": [] } }
    MAX_HISTORY = 20
    for vm in backend.get_all_vms():
        history[vm.id] = {
            "cpu": [vm.cpu],
            "mem": [vm.memory],
            "disk": [vm.disk],
        }

    def update_monitoring():
        vms = backend.get_all_vms()

        # Maintain history buffers
        for vm in vms:
            if vm.id not in history:
                history[vm.id] = {"cpu": [], "mem": [], "disk": []}

            h = history[vm.id]
            for key, val in [("cpu", vm.cpu), ("mem", vm.memory), ("disk", vm.disk)]:
                arr = h[key]
                arr.append(float(val))
                if len(arr) > MAX_HISTORY:
                    arr.pop(0)

        # Build CPU lines
        cpu_lines = []
        for vm in vms:
            cpu_lines.append(
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(
                            x=i,
                            y=y,
                            tooltip=f"{vm.name} CPU {y:.1f}%"
                        )
                        for i, y in enumerate(history[vm.id]["cpu"])
                    ],
                    color=ft.Colors.BLUE if vm.status == "running" else ft.Colors.GREY,
                    stroke_width=2,
                    curved=True,
                )
            )
        cpu_line_chart.lines = cpu_lines

        # Build Memory lines
        mem_lines = []
        for vm in vms:
            mem_lines.append(
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(
                            x=i,
                            y=y,
                            tooltip=f"{vm.name} MEM {y:.1f}%"
                        )
                        for i, y in enumerate(history[vm.id]["mem"])
                    ],
                    color=ft.Colors.GREEN if vm.status == "running" else ft.Colors.GREY,
                    stroke_width=2,
                    curved=True,
                )
            )
        mem_line_chart.lines = mem_lines

        # Build Disk lines
        disk_lines = []
        for vm in vms:
            disk_lines.append(
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(
                            x=i,
                            y=y,
                            tooltip=f"{vm.name} DISK {y:.1f}%"
                        )
                        for i, y in enumerate(history[vm.id]["disk"])
                    ],
                    color=ft.Colors.ORANGE if vm.status == "running" else ft.Colors.GREY,
                    stroke_width=2,
                    curved=True,
                )
            )
        disk_line_chart.lines = disk_lines

        # Update metrics table
        metrics_table.rows.clear()
        for vm in vms:
            metrics_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(vm.name)),
                        ft.DataCell(ft.Text(vm.status)),
                        ft.DataCell(ft.Text(f"{vm.cpu:.1f}%")),
                        ft.DataCell(ft.Text(f"{vm.memory:.1f}%")),
                        ft.DataCell(ft.Text(f"{vm.disk:.1f}%")),
                    ]
                )
            )

        page.update()




    
    def build_card(title_text: str, value_control, icon_name, bg_color=ft.Colors.GREY_100):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon_name, color=ft.Colors.BLUE_700),
                            ft.Text(title_text, size=14, color=ft.Colors.GREY_600),
                        ]
                    ),
                    value_control,
                ],
                spacing=10,
            ),
            padding=20,
            border_radius=10,
            bgcolor=bg_color,
            expand=True,
        )
    
    def build_progress_bar(label: str, value: float):
        color = ft.Colors.GREEN
        if value > 80:
            color = ft.Colors.RED
        elif value > 60:
            color = ft.Colors.ORANGE
            
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(f"{label}:", size=12, width=60),
                        ft.Text(f"{value:.1f}%", size=12, width=50),
                    ]
                ),
                ft.ProgressBar(
                    value=value/100,
                    color=color,
                    bgcolor=ft.Colors.GREY_300,
                    height=8,
                ),
            ],
            spacing=2,
        )
    
    def update_dashboard():
        vms = backend.get_all_vms()
        running = sum(1 for vm in vms if vm.status == "running")
        stopped = sum(1 for vm in vms if vm.status == "stopped")
        
        total_vms.value = str(len(vms))
        running_vms.value = str(running)
        stopped_vms.value = str(stopped)
        
        # Update activity log
        activity_log.controls.clear()
        activities = [
            f"{datetime.now().strftime('%H:%M')} - VM 'Web-Server-01' CPU usage high (85%)",
            f"{datetime.now().strftime('%H:%M')} - Backup completed for DB-Server-01",
            f"{datetime.now().strftime('%H:%M')} - New VM 'Dev-Env-02' created",
            f"{datetime.now().strftime('%H:%M')} - Security updates applied to 3 VMs",
        ]
        
        for activity in activities:
            activity_log.controls.append(
                ft.Text(activity, size=12)
            )
        
        page.update()
    
    def update_vm_list():
        vm_list_view.controls.clear()
        
        for vm in backend.get_all_vms():
            # Determine status color
            status_color = {
                "running": ft.Colors.GREEN,
                "stopped": ft.Colors.RED,
                "paused": ft.Colors.ORANGE,
                "creating": ft.Colors.BLUE,
                "starting": ft.Colors.YELLOW,
                "stopping": ft.Colors.ORANGE,
                "restarting": ft.Colors.YELLOW,
                "pausing": ft.Colors.ORANGE,
            }.get(vm.status, ft.Colors.GREY)
            
            vm_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.COMPUTER, color=ft.Colors.BLUE_700),
                                ft.Text(vm.name, size=16, weight=ft.FontWeight.W_500, expand=True),
                                ft.Container(
                                    content=ft.Text(vm.status.upper(), size=12, color=ft.Colors.WHITE),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=20,
                                ),
                            ]
                        ),
                        
                        ft.Divider(height=10),
                        
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("OS", size=12, color=ft.Colors.GREY_600),
                                        ft.Text(vm.os_type, size=14),
                                    ],
                                    expand=True,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("vCPU/RAM", size=12, color=ft.Colors.GREY_600),
                                        ft.Text(f"{vm.vcpu} vCPU / {vm.ram}", size=14),
                                    ],
                                    expand=True,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("IP Address", size=12, color=ft.Colors.GREY_600),
                                        ft.Text(vm.ip, size=14),
                                    ],
                                    expand=True,
                                ),
                            ]
                        ),
                        
                        ft.Divider(height=10),
                        
                        # Progress bars for resources
                        ft.Column(
                            controls=[
                                build_progress_bar("CPU", vm.cpu),
                                build_progress_bar("Memory", vm.memory),
                                build_progress_bar("Disk", vm.disk),
                            ],
                            spacing=5,
                        ),
                        
                        ft.Divider(height=10),
                        
                        # Action buttons
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.PLAY_ARROW if vm.status != "running" else ft.Icons.PAUSE,
                                    icon_color=ft.Colors.GREEN if vm.status != "running" else ft.Colors.ORANGE,
                                    on_click=lambda e, vm_id=vm.id: vm_action(vm_id, "start" if vm.status != "running" else "pause"),
                                    tooltip="Start" if vm.status != "running" else "Pause",
                                    disabled=vm.status in ["starting", "stopping", "restarting", "pausing", "creating"],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.STOP,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, vm_id=vm.id: vm_action(vm_id, "stop"),
                                    tooltip="Stop",
                                    disabled=vm.status != "running",
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    icon_color=ft.Colors.BLUE,
                                    on_click=lambda e, vm_id=vm.id: vm_action(vm_id, "restart"),
                                    tooltip="Restart",
                                    disabled=vm.status != "running",
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, vm_id=vm.id: delete_vm(vm_id),
                                    tooltip="Delete",
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=5,
                ),
                padding=15,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                bgcolor=ft.Colors.GREY_50,
            )
            
            vm_list_view.controls.append(vm_card)
        
        page.update()
    
    def create_vm(e):
        if not vm_name.value:
            creation_status.value = "Please enter a VM name!"
            creation_status.color = ft.Colors.RED
            page.update()
            return
        
        # Create VM
        vm = backend.create_vm(
            name=vm_name.value,
            os_type=os_type.value,
            vcpu=int(vcpu_count.value),
            ram=ram_size.value,
            storage=storage_size.value
        )
        
        creation_status.value = f"VM '{vm.name}' is being created..."
        creation_status.color = ft.Colors.BLUE
        
        # Clear form
        vm_name.value = ""
        
        # Update lists after a delay
        def delayed_update():
            time.sleep(3)
            update_vm_list()
            update_dashboard()
            creation_status.value = "VM created successfully!"
            creation_status.color = ft.Colors.GREEN
            page.update()
        
        threading.Thread(target=delayed_update, daemon=True).start()
        page.update()
    
    def vm_action(vm_id: int, action: str):
        success = backend.change_vm_status(vm_id, action)
        if success:
            status_bar.value = f"VM action '{action}' initiated..."
            update_vm_list()
        else:
            status_bar.value = "Action failed!"
        
        page.update()
    
    def delete_vm(vm_id: int):
        def confirm_delete(e):
            success = backend.delete_vm(vm_id)
            if success:
                status_bar.value = "VM deleted successfully!"
                update_vm_list()
                update_dashboard()
            else:
                status_bar.value = "Failed to delete VM!"
            
            page.dialog.open = False
            page.update()
        
        # Create confirmation dialog
        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this VM? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(page.dialog, 'open', False)),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.dialog = dlg
        dlg.open = True
        page.update()
    
    def refresh_vm_list(e):
        update_vm_list()
        status_bar.value = "VM list refreshed"
        page.update()
        
    def tab_changed(e):
        if tabs.selected_index == 0:  # Dashboard
            update_dashboard()
        elif tabs.selected_index == 1:  # VM List
            update_vm_list()
        elif tabs.selected_index == 3:  # Monitoring
            update_monitoring()
    
    def start_metrics_updater():
        def update_metrics():
            while True:
                time.sleep(3)
                backend.update_metrics()

                # Inject mock history data for each VM
                for vm in backend.get_all_vms():
                    if vm.id not in history:
                        history[vm.id] = {"cpu": [], "mem": [], "disk": []}

                    history[vm.id]["cpu"].append(vm.cpu)
                    history[vm.id]["mem"].append(vm.memory)
                    history[vm.id]["disk"].append(vm.disk)

                    # Keep only last MAX_HISTORY entries
                    for k in ["cpu", "mem", "disk"]:
                        if len(history[vm.id][k]) > MAX_HISTORY:
                            history[vm.id][k].pop(0)

                # Update UI depending on active tab
                if tabs.selected_index == 1:
                    update_vm_list()
                elif tabs.selected_index == 3:
                    update_monitoring()

        thread = threading.Thread(target=update_metrics, daemon=True)
        thread.start()

    # Build dashboard tab
    dashboard_tab = ft.Column(
        controls=[
            ft.Text("System Overview", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            
            # Summary cards row
            ft.Row(
                controls=[
                    build_card("Total VMs", total_vms, ft.Icons.COMPUTER),
                    build_card("Running", running_vms, ft.Icons.PLAY_ARROW, ft.Colors.GREEN_100),
                    build_card("Stopped", stopped_vms, ft.Icons.STOP, ft.Colors.RED_100),
                    build_card("Resource Usage", ft.Text("78%", size=36), ft.Icons.PIE_CHART, ft.Colors.BLUE_100),
                ],
                spacing=20,
            ),
            
            ft.Divider(height=20),
            
            # Recent Activity
            ft.Text("Recent Activity", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=activity_log,
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
            ),
        ],
        spacing=15,
    )
    
    # Build VM list tab
    vmlist_tab = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Virtual Machines", size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        on_click=refresh_vm_list,
                        tooltip="Refresh"
                    ),
                ]
            ),
            ft.Divider(height=10),
            vm_list_view,
        ],
        spacing=10,
        expand=True,
    )
    
    # Build create VM tab
    create_tab = ft.Column(
        controls=[
            ft.Text("Create New Virtual Machine", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
            
            ft.Row(controls=[vm_name], spacing=20),
            ft.Row(controls=[os_type, vcpu_count], spacing=20),
            ft.Row(controls=[ram_size, storage_size], spacing=20),
            
            ft.Divider(height=30),
            
            ft.ElevatedButton(
                text="Create Virtual Machine",
                icon=ft.Icons.ADD,
                on_click=create_vm,
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
                expand=True,
            ),
            creation_status,
        ],
        spacing=15,
        width=600,
    )
    
    # Build monitoring tab
    monitor_tab = ft.Column(
        controls=[
            ft.Text("Resource Monitoring", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),

            ft.Text("CPU Usage (%)", size=16, weight=ft.FontWeight.W_500),
            cpu_line_chart,

            ft.Divider(height=20),

            ft.Text("Memory Usage (%)", size=16, weight=ft.FontWeight.W_500),
            mem_line_chart,

            ft.Divider(height=20),

            ft.Text("Disk Usage (%)", size=16, weight=ft.FontWeight.W_500),
            disk_line_chart,

            ft.Divider(height=20),

            ft.Text("System Metrics", size=16, weight=ft.FontWeight.W_500),
            metrics_table,
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    
    # Create tab control
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Dashboard", 
                icon=ft.Icons.DASHBOARD,
                content=dashboard_tab
            ),
            ft.Tab(
                text="VM List", 
                icon=ft.Icons.LIST,
                content=vmlist_tab
            ),
            ft.Tab(
                text="Create VM", 
                icon=ft.Icons.ADD,
                content=create_tab
            ),
            ft.Tab(
                text="Monitoring", 
                icon=ft.Icons.MONITOR_HEART,
                content=monitor_tab
            ),
        ],
        expand=True,
        on_change=tab_changed
    )
    
    # Add all controls to page
    page.add(
        title,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        tabs,
        ft.Divider(height=10),
        status_bar,
    )
    
    # Initial updates
    update_dashboard()
    update_vm_list()
    update_monitoring()
    
    # Start metrics updater
    start_metrics_updater()

if __name__ == "__main__":
    ft.app(target=main)
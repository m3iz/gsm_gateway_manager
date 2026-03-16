import sys
import traceback

def test_import(module_name):
    try:
        __import__(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except Exception as e:
        print(f"❌ {module_name} - ERROR: {e}")
        traceback.print_exc()
        return False

print("="*50)
print("Тестирование импортов модулей")
print("="*50)

modules = [
    'utils.logger',
    'gsm.at_commands',
    'gsm.serial_manager',
    'gsm.gsm_modem',
    'gui.log_widget',
    'gui.connection_panel',
    'gui.sim_control',
    'gui.call_panel',
    'gui.sms_panel',
    'gui.scheduler_panel',
    'gui.statistics_panel',
    'gui.at_console',
    'gui.signal_graph',
    'gui.main_window'
]

for module in modules:
    test_import(module)

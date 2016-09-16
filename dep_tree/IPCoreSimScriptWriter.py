from __future__ import print_function
import time, os
import commands

from SmartOpen import SmartOpen
from DepFileParser import DepFileParser
from CommandLineParser import CommandLineParser
from Pathmaker import Pathmaker

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class IPCoreSimScriptWriter( object ):
  def __init__( self , aCommandLineArgs , aPathmaker ):
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker

  def write( self , aScriptVariables , aComponentPaths , aCommandList , aLibs, aMaps ):
    if not "device_top" in aScriptVariables:
      raise RuntimeError("Variable 'device_top' not defined.")

    # Hack alert : Alessandro
    code,output = commands.getstatusoutput('vsim -version')

    if 'modelsim' in output.lower():
    	print('ModelSim detected')
    	targetSimulator = 'ModelSim'
    	simulator = 'modelsim'
    elif 'questa' in output.lower():
    	print('Questa detected')
    	targetSimulator = 'Questa'
    	simulator = 'questa'
    else:
      raise RuntimeError("Failed to detect Modelsim/Questasim")

    with SmartOpen( self.CommandLineArgs.output ) as write:
      write("# Autogenerated project build script")
      write( time.strftime("# %c") )
      write( )

      # Hack alert : Alessandro
      write("set xlib $::env(XILINX_SIMLIBS)")

      lWorkingDir = os.path.abspath( os.path.join( os.path.split( self.CommandLineArgs.output )[0] , "top" ) )

      write("set outputDir {0}".format( lWorkingDir ))
      write("file mkdir $outputDir")

      # write("create_project top $outputDir -part {device_name}{device_package}{device_speed} -force".format( **aScriptVariables ) )
      write("create_project top $outputDir -force".format( **aScriptVariables ) )

      write('''
set obj [get_projects top]
set_property "default_lib" "xil_defaultlib" $obj
set_property "simulator_language" "Mixed" $obj
set_property "source_mgmt_mode" "DisplayOnly" $obj
set_property "target_language" "VHDL" $obj
''')

      write("set_property target_simulator "+targetSimulator+" [current_project]" )

      write("file mkdir $xlib" )
      lUnisim_nodebug = aScriptVariables.get('unisim_nodebug')
      if lUnisim_nodebug == '1': # If the encrypted library uses unisim
        if simulator == "questa": # Yeah... Incorrectly documented by Vivado They change the variable name used for questa on this option only.
          write("config_compile_simlib -cfgopt {questasim.vhdl.unisim: -nodebug}")
        else: write("config_compile_simlib -cfgopt {" + simulator + ".vhdl.unisim: -nodebug}")
      write("compile_simlib -simulator "+simulator+" -directory $xlib" )
      write("set_property compxlib.compiled_library_dir $xlib [current_project]" )

      write( )
      # write('set f [open "xil_ip_compile.tcl" w]' )
      for src in reversed( aCommandList["src"] ):
        lPath , lBasename = os.path.split( src.FilePath )
        lName, lExt = os.path.splitext( lBasename  )

        if lExt == ".xci" or lExt == ".edn":
          write("import_files -norecurse -fileset sources_1 {0}".format( src.FilePath ) )
          if lExt == ".xci":
            write("upgrade_ip [get_ips {0}]".format( lName ) )
            write("generate_target simulation [get_files {0}]".format( lBasename ) )
#TOPLVL
      write('''
exec mkdir -p {0}/{0}.srcs/sources_1/ip/built
exec touch .ipcores_sim_built'''.format(aScriptVariables['device_top']))
      write('''
set_property top top [get_filesets sim_1]
launch_simulation -scripts_only
cd {0}
exec echo exit | vsim -c -do top_compile.do -modelsimini modelsim.ini
'''.format( os.path.join( lWorkingDir , "top.sim/sim_1/behav" ) ) )
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

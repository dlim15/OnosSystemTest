#!/usr/bin/env python
'''
TODO: Document
'''


import time
import pexpect
import re
import traceback
sys.path.append("../")
from drivers.common.clidriver import CLI

class OnosDriver(CLI):

    def __init__(self):
        super(CLI, self).__init__()

    def connect(self,**connectargs):
        '''
        Creates ssh handle for ONOS "bench".
        '''
        try:
            for key in connectargs:
                vars(self)[key] = connectargs[key]
            self.home = "~/ONOS"
            for key in self.options:
                if key == "home":
                    self.home = self.options['home']
                    break


            self.name = self.options['name']
            self.handle = super(OnosCliDriver,self).connect(user_name = self.user_name, ip_address = self.ip_address,port = self.port, pwd = self.pwd, home = self.home)

            if self.handle:
                return self.handle
            else :
                main.log.info("NO ONOS HANDLE")
                return main.FALSE
        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":     " + self.handle.before)
            main.cleanup()
            main.exit()
        except:
            main.log.info(self.name + ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.log.error( traceback.print_exc() )
            main.log.info(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.cleanup()
            main.exit()

    def disconnect(self):
        '''
        Called when Test is complete to disconnect the ONOS handle.
        '''
        response = ''
        try:
            self.handle.sendline("exit")
            self.handle.expect("closed")
        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":     " + self.handle.before)
        except:
            main.log.error(self.name + ": Connection failed to the host")
            response = main.FALSE
        return response

    def onos_package(self):
        '''
        Produce a self-contained tar.gz file that can be deployed
        and executed on any platform with Java 7 JRE. 
        '''
        import os.path
        
        try:
            self.handle.sendline("onos-package")
            self.handle.expect("\$")
            handle = str(self.handle.before)
            main.log.info("onos-package command returned: "+
                    handle)
          
            #Create list out of the handle by partitioning 
            #spaces. 
            #NOTE: The last element of the list at the time
            #      of writing this function is the filepath
            #save this filepath for comparison later on
            temp_list = handle.split(" ")
            file_path = handle[-1:]
           
            #If last string contains the filepath, return
            # as success. 
            if "/tmp" in file_path:
                return main.TRUE
            else:
                return main.FALSE

        except:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":    " + self.handle.before)
        except:
            main.log.error("Failed to package ONOS")
            main.cleanup()
            main.exit()

    def clean_install(self):
        '''
        Runs mvn clean install in the root of the ONOS directory. 
        This will clean all ONOS artifacts then compile each module 

        Returns: main.TRUE on success 
        On Failure, exits the test
        '''
        try:
            self.handle.sendline("mvn clean install")
            while 1:
                i=self.handle.expect([
                    'There\sis\sinsufficient\smemory\sfor\sthe\sJava\s\
                            Runtime\sEnvironment\sto\scontinue',
                    'BUILD\sFAILURE',
                    'BUILD\sSUCCESS',
                    'ONOS\$',
                    pexpect.TIMEOUT],timeout=600)
                if i == 0:
                    main.log.error(self.name + ":There is insufficient memory \
                            for the Java Runtime Environment to continue.")
                    #return main.FALSE
                    main.cleanup()
                    main.exit()
                if i == 1:
                    main.log.error(self.name + ": Build failure!")
                    #return main.FALSE
                    main.cleanup()
                    main.exit()
                elif i == 2:
                    main.log.info(self.name + ": Build success!")
                elif i == 3:
                    main.log.info(self.name + ": Build complete")
                    self.handle.expect("\$", timeout=60)
                    return main.TRUE
                elif i == 4:
                    main.log.error(self.name + ": mvn clean install TIMEOUT!")
                    #return main.FALSE
                    main.cleanup()
                    main.exit()
                else:
                    main.log.error(self.name + ": unexpected response from \
                            mvn clean install")
                    #return main.FALSE
                    main.cleanup()
                    main.exit()
        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":     " + self.handle.before)
            main.cleanup()
            main.exit()
        except:
            main.log.info(self.name + ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.log.error( traceback.print_exc() )
            main.log.info(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.cleanup()
            main.exit()

    def git_pull(self, comp1=""):
        '''
        Assumes that "git pull" works without login
        
        This function will perform a git pull on the ONOS instance.
        If used as git_pull("NODE") it will do git pull + NODE. This is
        for the purpose of pulling from other nodes if necessary.

        Otherwise, this function will perform a git pull in the 
        ONOS repository. If it has any problems, it will return main.ERROR
        If it successfully does a git_pull, it will return a 1.
        If it has no updates, it will return a 0.

        '''
        try:
            # main.log.info(self.name + ": Stopping ONOS")
            #self.stop()
            self.handle.sendline("cd " + self.home)
            self.handle.expect("ONOS\$")
            if comp1=="":
                self.handle.sendline("git pull")
            else:
                self.handle.sendline("git pull " + comp1)
           
            uptodate = 0
            i=self.handle.expect(['fatal',
                'Username\sfor\s(.*):\s',
                '\sfile(s*) changed,\s',
                'Already up-to-date',
                'Aborting',
                'You\sare\snot\scurrently\son\sa\sbranch', 
                'You\sasked\sme\sto\spull\swithout\stelling\sme\swhich\sbranch\syou',
                'Pull\sis\snot\spossible\sbecause\syou\shave\sunmerged\sfiles',
                pexpect.TIMEOUT],
                timeout=300)
            #debug
           #main.log.report(self.name +": \n"+"git pull response: " + str(self.handle.before) + str(self.handle.after))
            if i==0:
                main.log.error(self.name + ": Git pull had some issue...")
                return main.ERROR
            elif i==1:
                main.log.error(self.name + ": Git Pull Asking for username. ")
                return main.ERROR
            elif i==2:
                main.log.info(self.name + ": Git Pull - pulling repository now")
                self.handle.expect("ONOS\$", 120)
                return 0
            elif i==3:
                main.log.info(self.name + ": Git Pull - Already up to date")
                return 1
            elif i==4:
                main.log.info(self.name + ": Git Pull - Aborting... Are there conflicting git files?")
                return main.ERROR
            elif i==5:
                main.log.info(self.name + ": Git Pull - You are not currently on a branch so git pull failed!")
                return main.ERROR
            elif i==6:
                main.log.info(self.name + ": Git Pull - You have not configured an upstream branch to pull from. Git pull failed!")
                return main.ERROR
            elif i==7:
                main.log.info(self.name + ": Git Pull - Pull is not possible because you have unmerged files.")
                return main.ERROR
            elif i==8:
                main.log.error(self.name + ": Git Pull - TIMEOUT")
                main.log.error(self.name + " Response was: " + str(self.handle.before))
                return main.ERROR
            else:
                main.log.error(self.name + ": Git Pull - Unexpected response, check for pull errors")
                return main.ERROR
        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":     " + self.handle.before)
            main.cleanup()
            main.exit()
        except:
            main.log.info(self.name + ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.log.error( traceback.print_exc() )
            main.log.info(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.cleanup()
            main.exit()

    def git_checkout(self, branch="master"):
        '''
        Assumes that "git pull" works without login
        
        This function will perform a git git checkout on the ONOS instance.
        If used as git_checkout("branch") it will do git checkout of the "branch".

        Otherwise, this function will perform a git checkout of the master
        branch of the ONOS repository. If it has any problems, it will return 
        main.ERROR. 
        If the branch was already the specified branch, or the git checkout was 
        successful then the function will return main.TRUE.

        '''
        try:
            # main.log.info(self.name + ": Stopping ONOS")
            #self.stop()
            self.handle.sendline("cd " + self.home)
            self.handle.expect("ONOS\$")
            if branch != 'master':
                #self.handle.sendline('git stash')
                #self.handle.expect('ONOS\$')
                #print "After issuing git stash cmnd: ", self.handle.before
                cmd = "git checkout "+branch
                print "checkout cmd = ", cmd
                self.handle.sendline(cmd)
                uptodate = 0
                i=self.handle.expect(['fatal',
                    'Username\sfor\s(.*):\s',
                    'Already\son\s\'',
                    'Switched\sto\sbranch\s\'', 
                    pexpect.TIMEOUT],timeout=60)
            else:
                #self.handle.sendline('git stash apply')
                #self.handle.expect('ONOS\$')
                #print "After issuing git stash apply cmnd: ", self.handle.before
                cmd = "git checkout "+branch
                print "checkout cmd = ", cmd
                self.handle.sendline(cmd)
                uptodate = 0
                switchedToMaster = 0
                i=self.handle.expect(['fatal',
                    'Username\sfor\s(.*):\s',
                    'Already\son\s\'master\'',
                    'Switched\sto\sbranch\s\'master\'', 
                    pexpect.TIMEOUT],timeout=60)
 

            if i==0:
                main.log.error(self.name + ": Git checkout had some issue...")
                return main.ERROR
            elif i==1:
                main.log.error(self.name + ": Git checkout Asking for username!!! Bad!")
                return main.ERROR
            elif i==2:
                main.log.info(self.name + ": Git Checkout %s : Already on this branch" %branch)
                self.handle.expect("ONOS\$")
                print "after checkout cmd = ", self.handle.before
                switchedToMaster = 1
                return main.TRUE
            elif i==3:
                main.log.info(self.name + ": Git checkout %s - Switched to this branch" %branch)
                self.handle.expect("ONOS\$")
                print "after checkout cmd = ", self.handle.before
                switchedToMaster = 1
                return main.TRUE
            elif i==4:
                main.log.error(self.name + ": Git Checkout- TIMEOUT")
                main.log.error(self.name + " Response was: " + str(self.handle.before))
                return main.ERROR
            else:
                main.log.error(self.name + ": Git Checkout - Unexpected response, check for pull errors")
                return main.ERROR

        except pexpect.EOF:
            main.log.error(self.name + ": EOF exception found")
            main.log.error(self.name + ":     " + self.handle.before)
            main.cleanup()
            main.exit()
        except:
            main.log.info(self.name + ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.log.error( traceback.print_exc() )
            main.log.info(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            main.cleanup()
            main.exit()

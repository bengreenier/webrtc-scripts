import os
import subprocess
import shutil
import itertools
from xml.etree import ElementTree as ET

from logger import Logger
from helper import convertToPlatformPath
import defaults
import userdef


class CreateNuget:
    """
    Creates .nuspec and .targets files that are needed for creating NuGet package
    for more info check out:
    https://docs.microsoft.com/en-us/nuget/guides/create-uwp-packages#create-and-update-the-nuspec-file

    Add, update, delete file elements in .nuspec based on configuration
    After making .nuspec and .targets run command -nuget pack WebRtc.nuspec
    using nuget_cli method, if you do not have nuget.exe download_nuget method
    will be run, which will download the latest nuget.exe file available
    """
    NUGET_FOLDER = '../webrtc/windows/nuget'
    NUSPEC_PATH = NUGET_FOLDER + '/WebRtc.nuspec'
    TARGETS_PATH = NUGET_FOLDER + '/WebRtc.targets'
    NUGET_TO_SCRIPTS = '../../../scripts/'

    NUGET_URL = 'https://dist.nuget.org/win-x86-commandline/latest/nuget.exe'
    NUGET_EXE_DST = NUGET_FOLDER + '/nuget.exe'

    NATIVE_LIB_SRC = '../webrtc/windows/solutions/Build/Output/Org.WebRtc/' + \
        '[CONFIGURATION]/[CPU]/[FILE]'
    NATIVE_LIB_TARGET = 'runtimes\\win10-[CPU]\\native'

    @classmethod
    def nuget_cli(cls, nuget_command, *args):
        """
        Adds nuget cli functionality to python script trough nuget.exe
        If nuget.exe is not available, download_nuget method is called

        :param nuget_command: nuget cli command can be writtenwith or without nuget prefix.
        :param *args: aditional options and arguments for the nuget cli command
        """

        if os.path.exists(cls.NUGET_EXE_DST):
            print('nuget.exe already downloaded')
        else:
            cls.download_nuget()

        if 'nuget ' in nuget_command:
            nuget_command = nuget_command.replace('nuget ', '')
            print(cls.NUGET_EXE_DST + ' ' + nuget_command)
        try:
            exe_path = convertToPlatformPath(
                os.path.dirname(os.path.abspath(__file__)) + '\\' + cls.NUGET_EXE_DST)
            full_command = [exe_path, nuget_command]
            for cmd in args:
                full_command.append(cmd)
            subprocess.call(full_command)
        except Exception as e:
            print(e)

    @staticmethod
    def download_nuget():
        """
        Download latest nuget.exe file from nuget.org
        """
        # Python 3:
        if CreateNuget.module_exists('urllib.request'):
            import urllib
            print('Downloading NuGet.exe file with urllib.request...')
            urllib.request.urlretrieve(CreateNuget.NUGET_URL, CreateNuget.NUGET_EXE_DST)

        # Python 2:
        if CreateNuget.module_exists('urllib2'):
            import urllib2
            print('Downloading NuGet.exe file with urllib2...')
            with open(CreateNuget.NUGET_EXE_DST, 'wb') as f:
                f.write(urllib2.urlopen(CreateNuget.NUGET_URL).read())
                f.close()
        print("Download Complete!")

    @staticmethod
    def module_exists(module_name):
        """
        :param module_name: name of the module that needs to be checked.
        :return: True/False based on if the input module exists or not
        """
        try:
            __import__(module_name)
        except ImportError:
            return False
        else:
            return True

    @classmethod
    def update_nuspec_files(cls, configuration, cpu, f_type=['.dll', '.pri'], target_path=False):
        """
        Updates existing file elements contained in .nuspec file
        :param configuration: Release or Debug.
        :param cpu: target cpu.
        :param f_type: array of file types to be updated (Default ['.dll', '.pri']).
        :param target_path: path for the target attribute of the file element that
            needs to be provided for all non default file types (.dll, .pri).
        """
        try:
            """
            in order for update to work nuspec must not have   xmlns="..."
            inside the package tag, otherwise files tag will not be found
            """
            with open(cls.NUSPEC_PATH, 'rb') as nuspec:
                tree = ET.parse(nuspec)
            files = tree.find('files')
            for element, ft in itertools.product(files, f_type):
                src_attrib = element.attrib.get('src')
                if all(val in src_attrib for val in [cpu, configuration, ft]):
                    f_name = 'Org.WebRtc' + ft
                    src_path = convertToPlatformPath(
                        cls.NATIVE_LIB_SRC
                        .replace('[CONFIGURATION]', configuration)
                        .replace('[CPU]', cpu)
                        .replace('[FILE]', f_name)
                    )
                    if target_path is False:
                        target_path = convertToPlatformPath(cls.NATIVE_LIB_TARGET.replace('[CPU]', cpu))
                    if os.path.exists(src_path):
                        src_path = convertToPlatformPath(cls.NUGET_TO_SCRIPTS + src_path)
                        element.set('src', src_path)
                        element.set('target', target_path)
                        tree.write(cls.NUSPEC_PATH)
                        print('nuspec file updated')
                    else:
                        raise Exception('File does NOT exist! \n' + src_path)
        except Exception as errorMessage:
            print(errorMessage)

    @classmethod
    def check_files(cls, configuration, cpu, f_type=['.dll', '.pri']):
        """
        Checks if file exists
        :param configuration: Release or Debug.
        :param cpu: target cpu.
        :param f_type: array of file types to be updated (Default ['.dll', '.pri']).
        """
        try:
            for ft in f_type:
                f_name = 'Org.WebRtc' + ft
                src_path = convertToPlatformPath(
                    cls.NATIVE_LIB_SRC
                    .replace('[CONFIGURATION]', configuration)
                    .replace('[CPU]', cpu)
                    .replace('[FILE]', f_name)
                )
                if os.path.exists(src_path):
                    print('File Exists! \n' + src_path)
                else:
                    print('File does NOT exist! \n' + src_path)
        except Exception as errorMessage:
            print(errorMessage)

    @classmethod
    def delete_nuspec_files(cls, configuration, cpu, f_type=['.dll', '.pri']):
        """
        Delete file element in .nuspec based on src attribute
        :param configuration: Release or Debug.
        :param cpu: target cpu.
        :param f_type: array of file types to be updated (Default ['.dll', '.pri']).
        """
        try:
            """
            in order for update to work nuspec must not have   xmlns="..."
            inside the package tag, otherwise files tag will not be found
            """
            with open(cls.NUSPEC_PATH, 'rb') as nuspec:
                tree = ET.parse(nuspec)
            files = tree.find('files')
            for element, ft in itertools.product(
                files, f_type
            ):
                src_attrib = element.attrib.get('src')
                target_attrib = element.attrib.get('target')
                tag = element.tag
                if all(val in src_attrib for val in [cpu, configuration, ft]):
                    files.remove(element)
                    print(
                        'File deleted: <{} src="{}" target="{}"/>'
                        .format(tag, src_attrib, target_attrib)
                    )
            tree.write(cls.NUSPEC_PATH)
        except Exception as errorMessage:
            print(errorMessage)

    @classmethod
    def add_nuspec_files(cls, configuration, cpu, f_type=['.dll', '.pri'], target_path=False):
        """
        Add file elements to .nuspec file based on config
        Every cpu type that you want to add to NuGet package must be built in
        eather Release or Debug configuration

        :param configuration: Release or Debug.
        :param cpu: target cpu.
        :param f_type: array of file types to be updated (Default ['.dll', '.pri']).
        :param target_path: path for the target attribute of the file element that
            needs to be provided for all non default file types (.dll, .pri).
        """
        try:
            """
            in order for update to work nuspec must not have   xmlns="..."
            inside the package tag, otherwise files tag will not be found
            """
            with open(cls.NUSPEC_PATH, 'rb') as nuspec:
                tree = ET.parse(nuspec)
            files = tree.find('files')
            for ft in f_type:
                f_name = 'Org.WebRtc' + ft
                src_path = convertToPlatformPath(
                    cls.NATIVE_LIB_SRC
                    .replace('[CONFIGURATION]', configuration)
                    .replace('[CPU]', cpu)
                    .replace('[FILE]', f_name)
                )
                if target_path is False:
                    target_path = convertToPlatformPath(cls.NATIVE_LIB_TARGET.replace('[CPU]', cpu))
                if os.path.exists(src_path):
                    src_path = convertToPlatformPath(cls.NUGET_TO_SCRIPTS + src_path)
                    file_attrib = {'src': src_path, 'target': target_path}
                    new_file = ET.SubElement(files, 'file', attrib=file_attrib)
                    new_file.tail = "\n\t\t"
                    print('File added: ' + str(file_attrib))
                else:
                    raise Exception('File does NOT exist! \n' + src_path)

            tree.write(cls.NUSPEC_PATH)
        except Exception as errorMessage:
            print(errorMessage)

    @classmethod
    def add_targets_itemgroup(
        cls, items_condition, sub_include, sub_elem='Reference',
        sub_sub_elem=False
    ):
        """
        Method used to change .targets file when making ORTC NuGet package
        delete_targets_itemgroups method must be run before adding itemgroups

        :param items_condition: Condition attribute for the ItemGroup element.
        :param sub_elem: sub element for the ItemGroup element(Default:'Reference').
        :param sub_include: Include attribute for the sub element
        :param sub_sub_elem: elements that are second level sub elements to
            ItemGroup element in a form of a dictionary (Optional)
            dictionary key is the element tag and value is element text
        """
        try:
            """
            in order for update to work targets must not have   xmlns="..."
            inside the Project tag, otherwise tag will not be found
            """
            with open(cls.TARGETS_PATH, 'rb') as targets:
                tree = ET.parse(targets)
            project = tree.getroot()
            new_itemgroup = ET.Element('ItemGroup')
            new_itemgroup.set('Condition', items_condition)
            new_itemgroup.text = '\n\t'
            element = ET.Element(sub_elem)
            sub_include = '$(MSBuildThisFileDirectory)' + sub_include
            element.set('Include', sub_include)
            if sub_sub_elem is not False:
                element.text = '\n\t'
                for key, val in sub_sub_elem.items():
                    sub_sub = ET.Element(key)
                    sub_sub.text = val
                    sub_sub.tail = '\n\t'
                    element.append(sub_sub)
            element.tail = '\n\t'
            new_itemgroup.append(element)
            new_itemgroup.tail = '\n\t'
            project.append(new_itemgroup)

            tree.write(cls.TARGETS_PATH)
        except Exception as errorMessage:
            print(errorMessage)

    @classmethod
    def delete_targets_itemgroups(cls):
        """
        Delete all ItemGroup elements from .targets file
        """
        try:
            with open(cls.TARGETS_PATH, 'rb') as targets:
                tree = ET.parse(targets)
            project = tree.getroot()
            for element in project:
                if 'ItemGroup' in element.tag:
                    project.remove(element)
            tree.write(cls.TARGETS_PATH)
            print('ItemGroups deleted')
        except Exception as errorMessage:
            print(errorMessage)

    @classmethod
    def create_nuspec(cls, version):
        """
        Create WebRtc.nuspec file based on a template with default values
        :param version: version of the nuget package must be specified when
        copying nuspec file
        """
        with open(cls.NUSPEC_PATH, 'w') as destination:
            with open(cls.NUGET_FOLDER + '/templates/WebRtc.nuspec', 'r') as source:
                for line in source:
                    if '<version>' in line:
                        destination.write('\t\t<version>' + version + '</version>\n')
                    else:
                        destination.write(line)
        print('nuspec created')

    @classmethod
    def create_targets(cls):
        """
        Create WebRtc.targets file based on a template with default values for WebRtc
        """
        with open(cls.TARGETS_PATH, 'w') as destination:
            with open(cls.NUGET_FOLDER + '/templates/WebRtc.targets', 'r') as source:
                for line in source:
                    destination.write(line)
        print('targets created')

    @classmethod
    def check_and_move(cls, version):
        """
        Checks if nuget package was made successfully and moves it to nuget folder
        """
        package = 'WebRtc.' + version + '.nupkg'
        if os.path.isfile(package):
            shutil.move(package, cls.NUGET_FOLDER + '/' + package)
        else:
            print('NuGet package does not exist')

    @classmethod
    def run(cls, version, cpus, configurations):
        """
        Method used to call all other methods in order necessary for create
            WebRtc NuGet package
        First creates .nuspec, then .targets then adds files to .nuspec
        based on parameters
        :param version: nuspec version.
        :param cpus: list of target cpus.
        :param configurations: Debug/Release.
        """
        cls.create_nuspec(version)
        cls.create_targets()
        for configuration, cpu in itertools.product(
            configurations, cpus
        ):
            cls.add_nuspec_files(configuration, cpu)
            cls.update_nuspec_files(
                configuration, cpu,
                f_type=['.winmd', '.xml'], target_path=r'lib\uap10.0'
            )
        cls.nuget_cli('pack', cls.NUGET_FOLDER + '/WebRtc.nuspec')
        cls.check_and_move(version)
        # cls.nuget_cli('help', '-All', '-Markdown')


def main():
    """
    WebRtc must be built for selected CPUs in userdef file before running
    """
    create_nuget = CreateNuget()
    create_nuget.run(
        '1.66.0.2-Alpha', userdef.targetCPUs, userdef.targetConfigurations
    )

if __name__ == '__main__':
    main()

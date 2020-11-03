# Copyright (c) 2020 Ultimaker B.V.
# Toolbox is released under the terms of the LGPLv3 or higher.

import json
import os
import tempfile
from typing import cast, Any, Dict, List, Set, TYPE_CHECKING, Tuple, Optional, Union

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from UM.Extension import Extension
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from UM.Version import Version
from UM.i18n import i18nCatalog
from cura import ApplicationMetadata
from cura.CuraApplication import CuraApplication
from cura.Machines.ContainerTree import ContainerTree
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .AuthorsModel import AuthorsModel
from .CloudApiModel import CloudApiModel
from .CloudSync.LicenseModel import LicenseModel
from .PackagesModel import PackagesModel

if TYPE_CHECKING:
    from UM.TaskManagement.HttpRequestData import HttpRequestData
    from cura.Settings.GlobalStack import GlobalStack

i18n_catalog = i18nCatalog("cura")

DEFAULT_MARKETPLACE_ROOT = "https://marketplace.ultimaker.com"  # type: str

try:
    from cura.CuraVersion import CuraMarketplaceRoot
except ImportError:
    CuraMarketplaceRoot = DEFAULT_MARKETPLACE_ROOT


class Toolbox(QObject, Extension):
    """Provides a marketplace for users to download plugins an materials"""

    def __init__(self, application: CuraApplication) -> None:
        super().__init__()

        self._application = application  # type: CuraApplication

        self._sdk_version = ApplicationMetadata.CuraSDKVersion  # type: Union[str, int]

        # Network:
        self._download_request_data = None  # type: Optional[HttpRequestData]
        self._download_progress = 0  # type: float
        self._is_downloading = False  # type: bool
        self._cloud_scope = UltimakerCloudScope(application)  # type: UltimakerCloudScope
        self._json_scope = JsonDecoratorScope(self._cloud_scope)  # type: JsonDecoratorScope

        self._request_urls = {}  # type: Dict[str, str]
        self._to_update = []  # type: List[str] # Package_ids that are waiting to be updated
        self._old_plugin_ids = set()  # type: Set[str]
        self._old_plugin_metadata = dict()  # type: Dict[str, Dict[str, Any]]

        # The responses as given by the server parsed to a list.
        self._server_response_data = {
            "authors":              [],
            "packages":             [],
            "updates":              []
        }  # type: Dict[str, List[Any]]

        # Models:
        self._models = {
            "authors":              AuthorsModel(self),
            "packages":             PackagesModel(self),
            "updates":              PackagesModel(self)
        }  # type: Dict[str, Union[AuthorsModel, PackagesModel]]

        self._plugins_showcase_model = PackagesModel(self)
        self._plugins_available_model = PackagesModel(self)
        self._plugins_installed_model = PackagesModel(self)
        self._plugins_installed_model.setFilter({"is_bundled": "False"})
        self._plugins_bundled_model = PackagesModel(self)
        self._plugins_bundled_model.setFilter({"is_bundled": "True"})
        self._materials_showcase_model = AuthorsModel(self)
        self._materials_available_model = AuthorsModel(self)
        self._materials_installed_model = PackagesModel(self)
        self._materials_installed_model.setFilter({"is_bundled": "False"})
        self._materials_bundled_model = PackagesModel(self)
        self._materials_bundled_model.setFilter({"is_bundled": "True"})
        self._materials_generic_model = PackagesModel(self)

        self._license_model = LicenseModel()

        # These properties are for keeping track of the UI state:
        # ----------------------------------------------------------------------
        # View category defines which filter to use, and therefore effectively
        # which category is currently being displayed. For example, possible
        # values include "plugin" or "material", but also "installed".
        self._view_category = "plugin"  # type: str

        # View page defines which type of page layout to use. For example,
        # possible values include "overview", "detail" or "author".
        self._view_page = "welcome"  # type: str

        # Active package refers to which package is currently being downloaded,
        # installed, or otherwise modified.
        self._active_package = None  # type: Optional[Dict[str, Any]]

        self._dialog = None  # type: Optional[QObject]
        self._confirm_reset_dialog = None  # type: Optional[QObject]
        self._resetUninstallVariables()

        self._restart_required = False  # type: bool

        # variables for the license agreement dialog
        self._license_dialog_plugin_file_location = ""  # type: str

        self._application.initializationFinished.connect(self._onAppInitialized)

    # Signals:
    # --------------------------------------------------------------------------
    # Downloading changes
    activePackageChanged = pyqtSignal()
    onDownloadProgressChanged = pyqtSignal()
    onIsDownloadingChanged = pyqtSignal()
    restartRequiredChanged = pyqtSignal()
    installChanged = pyqtSignal()
    enabledChanged = pyqtSignal()

    # UI changes
    viewChanged = pyqtSignal()
    detailViewChanged = pyqtSignal()
    filterChanged = pyqtSignal()
    metadataChanged = pyqtSignal()
    showLicenseDialog = pyqtSignal()
    closeLicenseDialog = pyqtSignal()
    uninstallVariablesChanged = pyqtSignal()

    def _restart(self):
        """Go back to the start state (welcome screen or loading if no login required)"""

        # For an Essentials build, login is mandatory
        if not self._application.getCuraAPI().account.isLoggedIn and ApplicationMetadata.IsEnterpriseVersion:
            self.setViewPage("welcome")
        else:
            self.setViewPage("loading")
            self._fetchPackageData()

    def _resetUninstallVariables(self) -> None:
        self._package_id_to_uninstall = None  # type: Optional[str]
        self._package_name_to_uninstall = ""
        self._package_used_materials = []  # type: List[Tuple[GlobalStack, str, str]]
        self._package_used_qualities = []  # type: List[Tuple[GlobalStack, str, str]]

    def getLicenseDialogPluginFileLocation(self) -> str:
        return self._license_dialog_plugin_file_location

    def openLicenseDialog(self, plugin_name: str, license_content: str, plugin_file_location: str, icon_url: str) -> None:
        # Set page 1/1 when opening the dialog for a single package
        self._license_model.setCurrentPageIdx(0)
        self._license_model.setPageCount(1)
        self._license_model.setIconUrl(icon_url)

        self._license_model.setPackageName(plugin_name)
        self._license_model.setLicenseText(license_content)
        self._license_dialog_plugin_file_location = plugin_file_location
        self.showLicenseDialog.emit()

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self) -> None:
        self._plugin_registry = self._application.getPluginRegistry()
        self._package_manager = self._application.getPackageManager()

        # We need to construct a query like installed_packages=ID:VERSION&installed_packages=ID:VERSION, etc.
        installed_package_ids_with_versions = [":".join(items) for items in
                                               self._package_manager.getAllInstalledPackageIdsAndVersions()]
        installed_packages_query = "&installed_packages=".join(installed_package_ids_with_versions)

        self._request_urls = {
            "authors": "{base_url}/authors".format(base_url = CloudApiModel.api_url),
            "packages": "{base_url}/packages".format(base_url = CloudApiModel.api_url),
            "updates": "{base_url}/packages/package-updates?installed_packages={query}".format(
                base_url = CloudApiModel.api_url, query = installed_packages_query)
        }

        self._application.getCuraAPI().account.loginStateChanged.connect(self._restart)

        # On boot we check which packages have updates.
        if CuraApplication.getInstance().getPreferences().getValue("info/automatic_update_check") and len(installed_package_ids_with_versions) > 0:
            # Request the latest and greatest!
            self._makeRequestByType("updates")


    def _fetchPackageData(self) -> None:
        self._makeRequestByType("packages")
        self._makeRequestByType("authors")
        self._updateInstalledModels()

    # Displays the toolbox
    @pyqtSlot()
    def launch(self) -> None:
        if not self._dialog:
            self._dialog = self._createDialog("Toolbox.qml")

        if not self._dialog:
            Logger.log("e", "Unexpected error trying to create the 'Marketplace' dialog.")
            return

        self._restart()

        self._dialog.show()
        # Apply enabled/disabled state to installed plugins
        self.enabledChanged.emit()

    def _createDialog(self, qml_name: str) -> Optional[QObject]:
        Logger.log("d", "Marketplace: Creating dialog [%s].", qml_name)
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if not plugin_path:
            return None
        path = os.path.join(plugin_path, "resources", "qml", qml_name)

        dialog = self._application.createQmlComponent(path, {
            "toolbox": self,
            "handler": self,
            "licenseModel": self._license_model
        })
        if not dialog:
            return None
        return dialog

    def _convertPluginMetadata(self, plugin_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            highest_sdk_version_supported = Version(0)
            for supported_version in plugin_data["plugin"]["supported_sdk_versions"]:
                if supported_version > highest_sdk_version_supported:
                    highest_sdk_version_supported = supported_version

            formatted = {
                "package_id": plugin_data["id"],
                "package_type": "plugin",
                "display_name": plugin_data["plugin"]["name"],
                "package_version": plugin_data["plugin"]["version"],
                "sdk_version": highest_sdk_version_supported,
                "author": {
                    "author_id": plugin_data["plugin"]["author"],
                    "display_name": plugin_data["plugin"]["author"]
                },
                "is_installed": True,
                "description": plugin_data["plugin"]["description"]
            }
            return formatted
        except KeyError:
            Logger.log("w", "Unable to convert plugin meta data %s", str(plugin_data))
            return None

    @pyqtSlot()
    def _updateInstalledModels(self) -> None:
        # This is moved here to avoid code duplication and so that after installing plugins they get removed from the
        # list of old plugins
        old_plugin_ids = self._plugin_registry.getInstalledPlugins()
        installed_package_ids = self._package_manager.getAllInstalledPackageIDs()
        scheduled_to_remove_package_ids = self._package_manager.getToRemovePackageIDs()

        self._old_plugin_ids = set()
        self._old_plugin_metadata = dict()

        for plugin_id in old_plugin_ids:
            # Neither the installed packages nor the packages that are scheduled to remove are old plugins
            if plugin_id not in installed_package_ids and plugin_id not in scheduled_to_remove_package_ids:
                Logger.log("d", "Found a plugin that was installed with the old plugin browser: %s", plugin_id)

                old_metadata = self._plugin_registry.getMetaData(plugin_id)
                new_metadata = self._convertPluginMetadata(old_metadata)
                if new_metadata is None:
                    # Something went wrong converting it.
                    continue
                self._old_plugin_ids.add(plugin_id)
                self._old_plugin_metadata[new_metadata["package_id"]] = new_metadata

        all_packages = self._package_manager.getAllInstalledPackagesInfo()
        if "plugin" in all_packages:
            # For old plugins, we only want to include the old custom plugin that were installed via the old toolbox.
            # The bundled plugins will be included in JSON files in the "bundled_packages" folder, so the bundled
            # plugins should be excluded from the old plugins list/dict.
            all_plugin_package_ids = set(package["package_id"] for package in all_packages["plugin"])
            self._old_plugin_ids = set(plugin_id for plugin_id in self._old_plugin_ids
                                    if plugin_id not in all_plugin_package_ids)
            self._old_plugin_metadata = {k: v for k, v in self._old_plugin_metadata.items() if k in self._old_plugin_ids}

            self._plugins_installed_model.setMetadata(all_packages["plugin"] + list(self._old_plugin_metadata.values()))
            self._plugins_bundled_model.setMetadata(all_packages["plugin"] + list(self._old_plugin_metadata.values()))
            self.metadataChanged.emit()
        if "material" in all_packages:
            self._materials_installed_model.setMetadata(all_packages["material"])
            self._materials_bundled_model.setMetadata(all_packages["material"])
            self.metadataChanged.emit()

    @pyqtSlot(str)
    def install(self, file_path: str) -> Optional[str]:
        package_id = self._package_manager.installPackage(file_path)
        self.installChanged.emit()
        self._updateInstalledModels()
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()
        return package_id

    @pyqtSlot(str)
    def checkPackageUsageAndUninstall(self, package_id: str) -> None:
        """Check package usage and uninstall

        If the package is in use, you'll get a confirmation dialog to set everything to default
        """

        package_used_materials, package_used_qualities = self._package_manager.getMachinesUsingPackage(package_id)
        if package_used_materials or package_used_qualities:
            # Set up "uninstall variables" for resetMaterialsQualitiesAndUninstall
            self._package_id_to_uninstall = package_id
            package_info = self._package_manager.getInstalledPackageInfo(package_id)
            self._package_name_to_uninstall = package_info.get("display_name", package_info.get("package_id"))
            self._package_used_materials = package_used_materials
            self._package_used_qualities = package_used_qualities
            # Ask change to default material / profile
            if self._confirm_reset_dialog is None:
                self._confirm_reset_dialog = self._createDialog("dialogs/ToolboxConfirmUninstallResetDialog.qml")
            self.uninstallVariablesChanged.emit()
            if self._confirm_reset_dialog is None:
                Logger.log("e", "ToolboxConfirmUninstallResetDialog should have been initialized, but it is not. Not showing dialog and not uninstalling package.")
            else:
                self._confirm_reset_dialog.show()
        else:
            # Plain uninstall
            self.uninstall(package_id)

    @pyqtProperty(str, notify = uninstallVariablesChanged)
    def pluginToUninstall(self) -> str:
        return self._package_name_to_uninstall

    @pyqtProperty(str, notify = uninstallVariablesChanged)
    def uninstallUsedMaterials(self) -> str:
        return "\n".join(["%s (%s)" % (str(global_stack.getName()), material) for global_stack, extruder_nr, material in self._package_used_materials])

    @pyqtProperty(str, notify = uninstallVariablesChanged)
    def uninstallUsedQualities(self) -> str:
        return "\n".join(["%s (%s)" % (str(global_stack.getName()), quality) for global_stack, extruder_nr, quality in self._package_used_qualities])

    @pyqtSlot()
    def closeConfirmResetDialog(self) -> None:
        if self._confirm_reset_dialog is not None:
            self._confirm_reset_dialog.close()

    @pyqtSlot()
    def resetMaterialsQualitiesAndUninstall(self) -> None:
        """Uses "uninstall variables" to reset qualities and materials, then uninstall

        It's used as an action on Confirm reset on Uninstall
        """

        application = CuraApplication.getInstance()
        machine_manager = application.getMachineManager()
        container_tree = ContainerTree.getInstance()

        for global_stack, extruder_nr, container_id in self._package_used_materials:
            extruder = global_stack.extruderList[int(extruder_nr)]
            approximate_diameter = extruder.getApproximateMaterialDiameter()
            variant_node = container_tree.machines[global_stack.definition.getId()].variants[extruder.variant.getName()]
            default_material_node = variant_node.preferredMaterial(approximate_diameter)
            machine_manager.setMaterial(extruder_nr, default_material_node, global_stack = global_stack)
        for global_stack, extruder_nr, container_id in self._package_used_qualities:
            variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
            material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
            extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
            definition_id = global_stack.definition.getId()
            machine_node = container_tree.machines[definition_id]
            default_quality_group = machine_node.getQualityGroups(variant_names, material_bases, extruder_enabled)[machine_node.preferred_quality_type]
            machine_manager.setQualityGroup(default_quality_group, global_stack = global_stack)

        if self._package_id_to_uninstall is not None:
            self._markPackageMaterialsAsToBeUninstalled(self._package_id_to_uninstall)
            self.uninstall(self._package_id_to_uninstall)
        self._resetUninstallVariables()
        self.closeConfirmResetDialog()

    @pyqtSlot()
    def onLicenseAccepted(self):
        self.closeLicenseDialog.emit()
        package_id = self.install(self.getLicenseDialogPluginFileLocation())


    @pyqtSlot()
    def onLicenseDeclined(self):
        self.closeLicenseDialog.emit()

    def _markPackageMaterialsAsToBeUninstalled(self, package_id: str) -> None:
        container_registry = self._application.getContainerRegistry()

        all_containers = self._package_manager.getPackageContainerIds(package_id)
        for container_id in all_containers:
            containers = container_registry.findInstanceContainers(id = container_id)
            if not containers:
                continue
            container = containers[0]
            if container.getMetaDataEntry("type") != "material":
                continue
            root_material_id = container.getMetaDataEntry("base_file")
            root_material_containers = container_registry.findInstanceContainers(id = root_material_id)
            if not root_material_containers:
                continue
            root_material_container = root_material_containers[0]
            root_material_container.setMetaDataEntry("removed", True)

    @pyqtSlot(str)
    def uninstall(self, package_id: str) -> None:
        self._package_manager.removePackage(package_id, force_add = True)
        self.installChanged.emit()
        self._updateInstalledModels()
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()

    def _update(self) -> None:
        """Actual update packages that are in self._to_update"""

        if self._to_update:
            plugin_id = self._to_update.pop(0)
            remote_package = self.getRemotePackage(plugin_id)
            if remote_package:
                download_url = remote_package["download_url"]
                Logger.log("d", "Updating package [%s]..." % plugin_id)
                self.startDownload(download_url)
            else:
                Logger.log("e", "Could not update package [%s] because there is no remote package info available.", plugin_id)

        if self._to_update:
            self._application.callLater(self._update)

    @pyqtSlot(str)
    def update(self, plugin_id: str) -> None:
        """Update a plugin by plugin_id"""

        self._to_update.append(plugin_id)
        self._application.callLater(self._update)

    @pyqtSlot(str)
    def enable(self, plugin_id: str) -> None:
        self._plugin_registry.enablePlugin(plugin_id)
        self.enabledChanged.emit()
        Logger.log("i", "%s was set as 'active'.", plugin_id)
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def disable(self, plugin_id: str) -> None:
        self._plugin_registry.disablePlugin(plugin_id)
        self.enabledChanged.emit()
        Logger.log("i", "%s was set as 'deactive'.", plugin_id)
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtProperty(bool, notify = metadataChanged)
    def dataReady(self) -> bool:
        return self._packages_model is not None

    @pyqtProperty(bool, notify = restartRequiredChanged)
    def restartRequired(self) -> bool:
        return self._restart_required

    @pyqtSlot()
    def restart(self) -> None:
        self._application.windowClosed()

    def getRemotePackage(self, package_id: str) -> Optional[Dict]:
        # TODO: make the lookup in a dict, not a loop. canUpdate is called for every item.
        remote_package = None
        for package in self._server_response_data["packages"]:
            if package["package_id"] == package_id:
                remote_package = package
                break
        return remote_package

    @pyqtSlot(str, result = bool)
    def canDowngrade(self, package_id: str) -> bool:
        # If the currently installed version is higher than the bundled version (if present), the we can downgrade
        # this package.
        local_package = self._package_manager.getInstalledPackageInfo(package_id)
        if local_package is None:
            return False

        bundled_package = self._package_manager.getBundledPackageInfo(package_id)
        if bundled_package is None:
            return False

        local_version = Version(local_package["package_version"])
        bundled_version = Version(bundled_package["package_version"])
        return bundled_version < local_version

    @pyqtSlot(str, result = bool)
    def isInstalled(self, package_id: str) -> bool:
        result = self._package_manager.isPackageInstalled(package_id)
        # Also check the old plugins list if it's not found in the package manager.
        if not result:
            result = self.isOldPlugin(package_id)
        return result

    @pyqtSlot(str, result = int)
    def getNumberOfInstalledPackagesByAuthor(self, author_id: str) -> int:
        count = 0
        for package in self._materials_installed_model.items:
            if package["author_id"] == author_id:
                count += 1
        return count

    # This slot is only used to get the number of material packages by author, not any other type of packages.
    @pyqtSlot(str, result = int)
    def getTotalNumberOfMaterialPackagesByAuthor(self, author_id: str) -> int:
        count = 0
        for package in self._server_response_data["packages"]:
            if package["package_type"] == "material":
                if package["author"]["author_id"] == author_id:
                    count += 1
        return count

    @pyqtSlot(str, result = bool)
    def isEnabled(self, package_id: str) -> bool:
        return package_id in self._plugin_registry.getActivePlugins()

    # Check for plugins that were installed with the old plugin browser
    def isOldPlugin(self, plugin_id: str) -> bool:
        return plugin_id in self._old_plugin_ids

    def getOldPluginPackageMetadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        return self._old_plugin_metadata.get(plugin_id)

    def isLoadingComplete(self) -> bool:
        populated = 0
        for metadata_list in self._server_response_data.items():
            if metadata_list:
                populated += 1
        return populated == len(self._server_response_data.items())

    # Make API Calls
    # --------------------------------------------------------------------------
    def _makeRequestByType(self, request_type: str) -> None:
        Logger.log("d", "Requesting [%s] metadata from server.", request_type)
        url = self._request_urls[request_type]

        callback = lambda r, rt = request_type: self._onDataRequestFinished(rt, r)
        error_callback = lambda r, e, rt = request_type: self._onDataRequestError(rt, r, e)
        self._application.getHttpRequestManager().get(url,
                                                      callback = callback,
                                                      error_callback = error_callback,
                                                      scope=self._json_scope)

    @pyqtSlot(str)
    def startDownload(self, url: str) -> None:
        Logger.log("i", "Attempting to download & install package from %s.", url)

        callback = lambda r: self._onDownloadFinished(r)
        error_callback = lambda r, e: self._onDownloadFailed(r, e)
        download_progress_callback = self._onDownloadProgress
        request_data = self._application.getHttpRequestManager().get(url,
                                                                     callback = callback,
                                                                     error_callback = error_callback,
                                                                     download_progress_callback = download_progress_callback,
                                                                     scope=self._cloud_scope
                                                                     )

        self._download_request_data = request_data
        self.setDownloadProgress(0)
        self.setIsDownloading(True)

    @pyqtSlot()
    def cancelDownload(self) -> None:
        Logger.log("i", "User cancelled the download of a package. request %s", self._download_request_data)
        if self._download_request_data is not None:
            self._application.getHttpRequestManager().abortRequest(self._download_request_data)
            self._download_request_data = None
        self.resetDownload()

    def resetDownload(self) -> None:
        self.setDownloadProgress(0)
        self.setIsDownloading(False)

    # Handlers for Network Events
    # --------------------------------------------------------------------------
    def _onDataRequestError(self, request_type: str, reply: "QNetworkReply", error: "QNetworkReply.NetworkError") -> None:
        Logger.log("e", "Request [%s] failed due to error [%s]: %s", request_type, error, reply.errorString())
        self.setViewPage("errored")

    def _onDataRequestFinished(self, request_type: str, reply: "QNetworkReply") -> None:
        if reply.operation() != QNetworkAccessManager.GetOperation:
            Logger.log("e", "_onDataRequestFinished() only handles GET requests but got [%s] instead", reply.operation())
            return

        http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if http_status_code != 200:
            Logger.log("e", "Request type [%s] got non-200 HTTP response: [%s]", http_status_code)
            self.setViewPage("errored")
            return

        data = bytes(reply.readAll())
        try:
            json_data = json.loads(data.decode("utf-8"))
        except json.decoder.JSONDecodeError:
            Logger.log("e", "Failed to decode response data as JSON for request type [%s], response data [%s]",
                       request_type, data)
            self.setViewPage("errored")
            return

        # Check for errors:
        if "errors" in json_data:
            for error in json_data["errors"]:
                Logger.log("e", "Request type [%s] got response showing error: %s", error["title"])
            self.setViewPage("errored")
            return

        # Create model and apply metadata:
        if not self._models[request_type]:
            Logger.log("e", "Could not find the model for request type [%s].", request_type)
            self.setViewPage("errored")
            return

        self._server_response_data[request_type] = json_data["data"]
        self._models[request_type].setMetadata(self._server_response_data[request_type])

        if request_type == "packages":
            self._models[request_type].setFilter({"type": "plugin"})
            self.reBuildMaterialsModels()
            self.reBuildPluginsModels()
            self._notifyPackageManager()
        elif request_type == "authors":
            self._models[request_type].setFilter({"package_types": "material"})
            self._models[request_type].setFilter({"tags": "generic"})
        elif request_type == "updates":
            # Tell the package manager that there's a new set of updates available.
            packages = set([pkg["package_id"] for pkg in self._server_response_data[request_type]])
            self._package_manager.setPackagesWithUpdate(packages)

        self.metadataChanged.emit()

        if self.isLoadingComplete():
            self.setViewPage("overview")

    # This function goes through all known remote versions of a package and notifies the package manager of this change
    def _notifyPackageManager(self):
        for package in self._server_response_data["packages"]:
            self._package_manager.addAvailablePackageVersion(package["package_id"], Version(package["package_version"]))

    def _onDownloadFinished(self, reply: "QNetworkReply") -> None:
        self.resetDownload()

        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("w", "Failed to download package. The following error was returned: %s",
                       json.loads(reply.readAll().data().decode("utf-8")))
            return
        # Must not delete the temporary file on Windows
        self._temp_plugin_file = tempfile.NamedTemporaryFile(mode = "w+b", suffix = ".curapackage", delete = False)
        file_path = self._temp_plugin_file.name
        # Write first and close, otherwise on Windows, it cannot read the file
        self._temp_plugin_file.write(reply.readAll())
        self._temp_plugin_file.close()
        self._onDownloadComplete(file_path)

    def _onDownloadFailed(self, reply: "QNetworkReply", error: "QNetworkReply.NetworkError") -> None:
        Logger.log("w", "Failed to download package. The following error was returned: %s", error)

        self.resetDownload()

    def _onDownloadProgress(self, bytes_sent: int, bytes_total: int) -> None:
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            self.setDownloadProgress(new_progress)
            Logger.log("d", "new download progress %s / %s : %s%%", bytes_sent, bytes_total, new_progress)

    def _onDownloadComplete(self, file_path: str) -> None:
        Logger.log("i", "Download complete.")
        package_info = self._package_manager.getPackageInfo(file_path)
        if not package_info:
            Logger.log("w", "Package file [%s] was not a valid CuraPackage.", file_path)
            return

        license_content = self._package_manager.getPackageLicense(file_path)
        package_id = package_info["package_id"]
        if license_content is not None:
            # get the icon url for package_id, make sure the result is a string, never None
            icon_url = next((x["icon_url"] for x in self.packagesModel.items if x["id"] == package_id), None) or ""
            self.openLicenseDialog(package_info["display_name"], license_content, file_path, icon_url)
            return

        installed_id = self.install(file_path)
        if installed_id != package_id:
            Logger.error("Installed package {} does not match {}".format(installed_id, package_id))

    # Getter & Setters for Properties:
    # --------------------------------------------------------------------------
    def setDownloadProgress(self, progress: float) -> None:
        if progress != self._download_progress:
            self._download_progress = progress
            self.onDownloadProgressChanged.emit()

    @pyqtProperty(int, fset = setDownloadProgress, notify = onDownloadProgressChanged)
    def downloadProgress(self) -> float:
        return self._download_progress

    def setIsDownloading(self, is_downloading: bool) -> None:
        if self._is_downloading != is_downloading:
            self._is_downloading = is_downloading
            self.onIsDownloadingChanged.emit()

    @pyqtProperty(bool, fset = setIsDownloading, notify = onIsDownloadingChanged)
    def isDownloading(self) -> bool:
        return self._is_downloading

    def setActivePackage(self, package: QObject) -> None:
        if self._active_package != package:
            self._active_package = package
            self.activePackageChanged.emit()

    @pyqtProperty(QObject, fset = setActivePackage, notify = activePackageChanged)
    def activePackage(self) -> Optional[QObject]:
        """The active package is the package that is currently being downloaded"""

        return self._active_package

    def setViewCategory(self, category: str = "plugin") -> None:
        if self._view_category != category:
            self._view_category = category
            self.viewChanged.emit()

    # Function explicitly defined so that it can be called through the callExtensionsMethod
    # which cannot receive arguments.
    def setViewCategoryToMaterials(self) -> None:
        self.setViewCategory("material")

    @pyqtProperty(str, fset = setViewCategory, notify = viewChanged)
    def viewCategory(self) -> str:
        return self._view_category

    def setViewPage(self, page: str = "overview") -> None:
        if self._view_page != page:
            self._view_page = page
            self.viewChanged.emit()

    @pyqtProperty(str, fset = setViewPage, notify = viewChanged)
    def viewPage(self) -> str:
        return self._view_page

    # Exposed Models:
    # --------------------------------------------------------------------------
    @pyqtProperty(QObject, constant = True)
    def authorsModel(self) -> AuthorsModel:
        return cast(AuthorsModel, self._models["authors"])

    @pyqtProperty(QObject, constant = True)
    def packagesModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["packages"])

    @pyqtProperty(QObject, constant = True)
    def pluginsShowcaseModel(self) -> PackagesModel:
        return self._plugins_showcase_model

    @pyqtProperty(QObject, constant = True)
    def pluginsAvailableModel(self) -> PackagesModel:
        return self._plugins_available_model

    @pyqtProperty(QObject, constant = True)
    def pluginsInstalledModel(self) -> PackagesModel:
        return self._plugins_installed_model

    @pyqtProperty(QObject, constant = True)
    def pluginsBundledModel(self) -> PackagesModel:
        return self._plugins_bundled_model

    @pyqtProperty(QObject, constant = True)
    def materialsShowcaseModel(self) -> AuthorsModel:
        return self._materials_showcase_model

    @pyqtProperty(QObject, constant = True)
    def materialsAvailableModel(self) -> AuthorsModel:
        return self._materials_available_model

    @pyqtProperty(QObject, constant = True)
    def materialsInstalledModel(self) -> PackagesModel:
        return self._materials_installed_model

    @pyqtProperty(QObject, constant = True)
    def materialsBundledModel(self) -> PackagesModel:
        return self._materials_bundled_model

    @pyqtProperty(QObject, constant = True)
    def materialsGenericModel(self) -> PackagesModel:
        return self._materials_generic_model

    @pyqtSlot(str, result = str)
    def getWebMarketplaceUrl(self, page: str) -> str:
        root = CuraMarketplaceRoot
        if root == "":
            root = DEFAULT_MARKETPLACE_ROOT
        return root + "/app/cura/" + page

    # Filter Models:
    # --------------------------------------------------------------------------
    @pyqtSlot(str, str, str)
    def filterModelByProp(self, model_type: str, filter_type: str, parameter: str) -> None:
        if not self._models[model_type]:
            Logger.log("w", "Couldn't filter %s model because it doesn't exist.", model_type)
            return
        self._models[model_type].setFilter({filter_type: parameter})
        self.filterChanged.emit()

    @pyqtSlot(str, "QVariantMap")
    def setFilters(self, model_type: str, filter_dict: dict) -> None:
        if not self._models[model_type]:
            Logger.log("w", "Couldn't filter %s model because it doesn't exist.", model_type)
            return
        self._models[model_type].setFilter(filter_dict)
        self.filterChanged.emit()

    @pyqtSlot(str)
    def removeFilters(self, model_type: str) -> None:
        if not self._models[model_type]:
            Logger.log("w", "Couldn't remove filters on %s model because it doesn't exist.", model_type)
            return
        self._models[model_type].setFilter({})
        self.filterChanged.emit()

    # HACK(S):
    # --------------------------------------------------------------------------
    def reBuildMaterialsModels(self) -> None:
        materials_showcase_metadata = []
        materials_available_metadata = []
        materials_generic_metadata = []

        processed_authors = []  # type: List[str]

        for item in self._server_response_data["packages"]:
            if item["package_type"] == "material":

                author = item["author"]
                if author["author_id"] in processed_authors:
                    continue

                # Generic materials to be in the same section
                if "generic" in item["tags"]:
                    materials_generic_metadata.append(item)
                else:
                    if "showcase" in item["tags"]:
                        materials_showcase_metadata.append(author)
                    else:
                        materials_available_metadata.append(author)

                    processed_authors.append(author["author_id"])

        self._materials_showcase_model.setMetadata(materials_showcase_metadata)
        self._materials_available_model.setMetadata(materials_available_metadata)
        self._materials_generic_model.setMetadata(materials_generic_metadata)

    def reBuildPluginsModels(self) -> None:
        plugins_showcase_metadata = []
        plugins_available_metadata = []

        for item in self._server_response_data["packages"]:
            if item["package_type"] == "plugin":
                if "showcase" in item["tags"]:
                    plugins_showcase_metadata.append(item)
                else:
                    plugins_available_metadata.append(item)

        self._plugins_showcase_model.setMetadata(plugins_showcase_metadata)
        self._plugins_available_model.setMetadata(plugins_available_metadata)

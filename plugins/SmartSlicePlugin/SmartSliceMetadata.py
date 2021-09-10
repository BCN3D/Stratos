import os
import json
from typing import Optional, Dict

from .SmartSliceAuth import AuthConfiguration

class PluginMetaData:
    def __init__(self) -> None:
        self.name = "SmartSlice Plugin"
        self.id = "SmartSlicePlugin"
        self.version = "N/A"
        self.url = "https://api.smartslice.xyz"
        self.account = "https://account.tetonsim.com"
        self.cluster = None
        self.auth_config = AuthConfiguration()

        self.client_name = "cura"
        self.home_page = "https://tetonsim.com"
        self.product_page = "https://www.tetonsim.com/smart-slice-for-cura"
        self.help_page = "https://help.tetonsim.com"
        self.help_email = "mailto:help@tetonsim.com"

        pluginMetaData = PluginMetaData.getMetadata()

        if pluginMetaData:
            self.name = pluginMetaData.get("name", self.name)
            self.id = pluginMetaData.get("id", self.id)
            self.version = pluginMetaData.get("version", self.version)
            self.account = pluginMetaData.get("smartSliceAccount", self.account)
            self.home_page = pluginMetaData.get("smartSliceHome", self.home_page)

            apiInfo = pluginMetaData.get("smartSliceApi", None)

            if apiInfo:
                self.url = apiInfo.get("url", self.url)
                self.cluster = apiInfo.get("cluster", self.cluster)

            auth = pluginMetaData.get('smartSliceAuth')

            if auth:
                basic_auth = auth.get('basicAuth', False)
                client_id = auth.get('clientId', 'smartslice-cura')
                redirect_ports = auth.get('redirectPorts')
                oauth_basic = auth.get('oauthBasic', True)
                oauth_providers = auth.get('oauthProviders', [])

                self.auth_config = AuthConfiguration(
                    basic_auth, client_id, redirect_ports, oauth_basic, oauth_providers
                )

            product_info = pluginMetaData.get('smartSliceProductInfo')

            if product_info:
                self.client_name = product_info.get('clientName', self.client_name)
                self.home_page = product_info.get('homePage', self.home_page)
                self.help_page = product_info.get('helpPage', self.help_page)
                self.help_email = product_info.get('helpEmail', self.help_email)

    @staticmethod
    def getMetadata() -> Optional[Dict[str, str]]:
        try:
            plugin_json_path = os.path.dirname(os.path.abspath(__file__))
            plugin_json_path = os.path.join(plugin_json_path, "plugin.json")
            with open(plugin_json_path, "r") as f:
                plugin_info = json.load(f)
            return plugin_info
        except:
            return None

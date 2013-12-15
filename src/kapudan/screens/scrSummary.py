# -*- coding: utf-8 -*-
#
# Copyright (C) 2012, The Chakra Developers
#
# This is a fork of Pardus's Kaptan, which is
# Copyright (C) 2005-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from PyQt4 import QtGui
from PyQt4.QtCore import QString  # remove usage of QString
from PyQt4.QtGui import QMessageBox
from PyKDE4.kdecore import i18n, KConfig

import subprocess
import os
import dbus
import time

from kapudan.screen import Screen
from kapudan.screens.ui_scrSummary import Ui_summaryWidget
from PyKDE4 import kdeui

# import other widgets to get the latest configuration
#import kapudan.screens.scrFolder as folderWidget
import kapudan.screens.scrWallpaper as wallpaperWidget
import kapudan.screens.scrMouse as mouseWidget
import kapudan.screens.scrStyle as styleWidget
import kapudan.screens.scrMenu as menuWidget
import kapudan.screens.scrPackage as packageWidget
import kapudan.screens.scrServices as servicesWidget
import kapudan.screens.scrSecurity as securityWidget

#from kapudan.tools import tools
from kapudan.tools.spunrc import SpunRC
from kapudan.tools.daemon import Daemon


class Widget(QtGui.QWidget, Screen):
    title = i18n("Summary")
    desc = i18n("Save Your Settings")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, None)
        self.ui = Ui_summaryWidget()
        self.ui.setupUi(self)

    def shown(self):
        self.wallpaperSettings = wallpaperWidget.Widget.screenSettings
        self.mouseSettings = mouseWidget.Widget.screenSettings
        self.menuSettings = menuWidget.Widget.screenSettings
        self.styleSettings = styleWidget.Widget.screenSettings
        self.packageSettings = packageWidget.Widget.screenSettings
        self.servicesSettings = servicesWidget.Widget.screenSettings
        self.securitySettings = securityWidget.Widget.screenSettings

        subject = "<p><li><b>%s</b></li><ul>"
        item = "<li>%s</li>"
        end = "</ul></p>"
        content = QString("")

        content.append("""<html><body><ul>""")

        # Mouse Settings
        content.append(subject % i18n("Mouse Settings"))

        content.append(item % i18n("Selected Mouse configuration: <b>%s</b>") % self.mouseSettings["summaryMessage"]["selectedMouse"])
        content.append(item % i18n("Selected clicking behavior: <b>%s</b>") % self.mouseSettings["summaryMessage"]["clickBehavior"])
        content.append(end)

        # Menu Settings
        content.append(subject % i18n("Menu Settings"))
        content.append(item % i18n("Selected Menu: <b>%s</b>") % self.menuSettings["summaryMessage"])
        content.append(end)

        # Wallpaper Settings
        content.append(subject % i18n("Wallpaper Settings"))
        if not self.wallpaperSettings["hasChanged"]:
            content.append(item % i18n("You haven't selected any wallpaper."))
        else:
            content.append(item % i18n("Selected Wallpaper: <b>%s</b>") % os.path.basename(str(self.wallpaperSettings["selectedWallpaper"])))
        content.append(end)

        # Style Settings
        content.append(subject % i18n("Style Settings"))

        if not self.styleSettings["hasChanged"]:
            content.append(item % i18n("You haven't selected any style."))
        else:
            content.append(item % i18n("Selected Style: <b>%s</b>") % unicode(self.styleSettings["summaryMessage"]))

        content.append(end)

        # Spun Settings
        if self.packageSettings["hasChanged"]:
            content.append(subject % i18n("Package Management Settings"))
            content.append(item % i18n("You have enabled or disabled spun."))

            content.append(end)

        # Services Settings
        if self.servicesSettings["hasChanged"]:
            self.daemon = Daemon()
            self.svctext = i18n("You have: ")
            self.svcissset = False
            content.append(subject % i18n("Services Settings"))

            if self.servicesSettings["enableCups"] and not self.daemon.isEnabled("cups"):
                self.svctext += i18n("enabled cups; ")
                self.svcisset = True
            elif not self.servicesSettings["enableCups"] and self.daemon.isEnabled("cups"):
                self.svctext += i18n("disabled cups; ")
                self.svcisset = True
            if self.servicesSettings["enableBluetooth"] and not self.daemon.isEnabled("bluetooth"):
                self.svctext += i18n("enabled bluetooth; ")
                self.svcisset = True
            elif not self.servicesSettings["enableBluetooth"] and self.daemon.isEnabled("bluetooth"):
                self.svctext += i18n("disabled bluetooth; ")
                self.svcisset = True

            #FIXME: when can this ever happen?
            if not self.svcisset:
                self.svctext = i18n("You have made no changes.")
                self.servicesSettings["hasChanged"] = False

            content.append(item % i18n(self.svctext))

            content.append(end)

        # Security Settings
        if self.securitySettings["hasChanged"]:
            self.daemon = Daemon()
            self.sectext = i18n("You have: ")
            self.secisset = False
            content.append(subject % i18n("Security Settings"))

            if self.securitySettings["enableClam"] and not self.daemon.isEnabled("clamd"):
                self.sectext += i18n("enabled ClamAV; ")
                self.secisset = True
            elif not self.securitySettings["enableClam"] and self.daemon.isEnabled("clamd"):
                self.sectext += i18n("disabled ClamAV; ")
                self.secisset = True
            if self.securitySettings["enableFire"] and not self.daemon.isEnabled("ufw"):
                self.sectext += i18n("enabled the firewall; ")
                self.secisset = True
            elif not self.securitySettings["enableFire"] and self.daemon.isEnabled("ufw"):
                self.sectext += i18n("disabled the firewall; ")
                self.secisset = True

            if not self.secisset:
                self.sectext = i18n("You have made no changes.")
                self.securitySettings["hasChanged"] = False

            content.append(item % i18n(self.sectext))

            content.append(end)

        self.ui.textSummary.setText(content)

    def killPlasma(self):
        try:
            p = subprocess.Popen(["kquitapp", "plasma-desktop"], stdout=subprocess.PIPE)
            out, err = p.communicate()
            time.sleep(1)
            self.startPlasma()

        except:
            QMessageBox.critical(self, i18n("Error"), i18n("Cannot restart plasma-desktop. Kapudan will now shut down."))
            kdeui.KApplication.kApplication().quit()

    def startPlasma(self):
        subprocess.Popen(["plasma-desktop"], stdout=subprocess.PIPE)

    def execute(self):
        hasChanged = False
        rootActions = ""

        # Wallpaper Settings
        if self.wallpaperSettings["hasChanged"]:
            hasChanged = True
            if self.wallpaperSettings["selectedWallpaper"]:
                config = KConfig("plasma-desktop-appletsrc")
                group = config.group("Containments")
                for each in list(group.groupList()):
                    subgroup = group.group(each)
                    subcomponent = subgroup.readEntry('plugin')
                    if subcomponent == 'desktop' or subcomponent == 'folderview':
                        subg = subgroup.group('Wallpaper')
                        subg_2 = subg.group('image')
                        subg_2.writeEntry("wallpaper", self.wallpaperSettings["selectedWallpaper"])

        # Menu Settings
        if self.menuSettings["hasChanged"]:
            hasChanged = True
            config = KConfig("plasma-desktop-appletsrc")
            group = config.group("Containments")

            for each in list(group.groupList()):
                subgroup = group.group(each)
                subcomponent = subgroup.readEntry('plugin')
                if subcomponent == 'panel':
                    subg = subgroup.group('Applets')
                    for i in list(subg.groupList()):
                        subg2 = subg.group(i)
                        launcher = subg2.readEntry('plugin')
                        if str(launcher).find('launcher') >= 0:
                            subg2.writeEntry('plugin', self.menuSettings["selectedMenu"])

        def removeFolderViewWidget():
            config = KConfig("plasma-desktop-appletsrc")

            sub_lvl_0 = config.group("Containments")

            for sub in list(sub_lvl_0.groupList()):
                sub_lvl_1 = sub_lvl_0.group(sub)

                if sub_lvl_1.hasGroup("Applets"):
                    sub_lvl_2 = sub_lvl_1.group("Applets")

                    for sub2 in list(sub_lvl_2.groupList()):
                        sub_lvl_3 = sub_lvl_2.group(sub2)
                        plugin = sub_lvl_3.readEntry('plugin')

                        if plugin == 'folderview':
                            sub_lvl_3.deleteGroup()

        # Desktop Type
        if self.styleSettings["hasChangedDesktopType"]:
            hasChanged = True
            config = KConfig("plasma-desktop-appletsrc")
            group = config.group("Containments")

            for each in list(group.groupList()):
                subgroup = group.group(each)
                subcomponent = subgroup.readEntry('plugin')
                subcomponent2 = subgroup.readEntry('screen')
                if subcomponent == 'desktop' or subcomponent == 'folderview':
                    if int(subcomponent2) == 0:
                        subgroup.writeEntry('plugin', self.styleSettings["desktopType"])

            # Remove folder widget - normally this would be done over dbus but thanks to improper naming of the plasma interface
            # this is not possible
            # ValueError: Invalid interface or error name 'org.kde.plasma-desktop': contains invalid character '-'
            #
            # Related Bug:
            # Bug 240358 - Invalid D-BUS interface name 'org.kde.plasma-desktop.PlasmaApp' found while parsing introspection
            # https://bugs.kde.org/show_bug.cgi?id=240358

            if self.styleSettings["desktopType"] == "folderview":
                removeFolderViewWidget()

            config.sync()

        # Number of Desktops
        if self.styleSettings["hasChangedDesktopNumber"]:
            hasChanged = True
            config = KConfig("kwinrc")
            group = config.group("Desktops")
            group.writeEntry('Number', self.styleSettings["desktopNumber"])
            group.sync()

            info = kdeui.NETRootInfo(QtGui.QX11Info.display(), kdeui.NET.NumberOfDesktops | kdeui.NET.DesktopNames)
            info.setNumberOfDesktops(int(self.styleSettings["desktopNumber"]))
            info.activate()

            session = dbus.SessionBus()

            try:
                proxy = session.get_object('org.kde.kwin', '/KWin')
                proxy.reconfigure()
            except dbus.DBusException:
                pass

            config.sync()

        def deleteIconCache():
            try:
                os.remove("/var/tmp/kdecache-%s/icon-cache.kcache" % os.environ.get("USER"))
            except:
                pass

            for i in range(kdeui.KIconLoader.LastGroup):
                kdeui.KGlobalSettings.self().emitChange(kdeui.KGlobalSettings.IconChanged, i)

        # Theme Settings
        if self.styleSettings["hasChanged"]:
#            if self.styleSettings["iconChanged"]:
#                hasChanged = True
#                configKdeGlobals = KConfig("kdeglobals")
#                group = configKdeGlobals.group("General")
#
#                groupIconTheme = configKdeGlobals.group("Icons")
#                groupIconTheme.writeEntry("Theme", self.styleSettings["iconTheme"])
#
#                configKdeGlobals.sync()
#
#                # Change Icon theme
#                kdeui.KIconTheme.reconfigure()
#                kdeui.KIconCache.deleteCache()
#                deleteIconCache()

            if self.styleSettings["styleChanged"]:
                hasChanged = True
                configKdeGlobals = KConfig("kdeglobals")
                group = configKdeGlobals.group("General")
                group.writeEntry("widgetStyle", self.styleSettings["styleDetails"][unicode(self.styleSettings["styleName"])]["widgetStyle"])

                #groupIconTheme = configKdeGlobals.group("Icons")
                #groupIconTheme.writeEntry("Theme", self.styleSettings["iconTheme"])
                #groupIconTheme.writeEntry("Theme", self.styleSettings["styleDetails"][unicode(self.styleSettings["styleName"])]["iconTheme"])

                configKdeGlobals.sync()

                # Change Icon theme
                kdeui.KIconTheme.reconfigure()
                kdeui.KIconCache.deleteCache()
                deleteIconCache()

                for i in range(kdeui.KIconLoader.LastGroup):
                    kdeui.KGlobalSettings.self().emitChange(kdeui.KGlobalSettings.IconChanged, i)

                # Change widget style & color
                for key, value in self.styleSettings["styleDetails"][unicode(self.styleSettings["styleName"])]["colorScheme"].items():
                    colorGroup = configKdeGlobals.group(key)
                    for key2, value2 in value.items():
                            colorGroup.writeEntry(str(key2), str(value2))

                configKdeGlobals.sync()
                kdeui.KGlobalSettings.self().emitChange(kdeui.KGlobalSettings.StyleChanged)

                configPlasmaRc = KConfig("plasmarc")
                groupDesktopTheme = configPlasmaRc.group("Theme")
                groupDesktopTheme.writeEntry("name", self.styleSettings["styleDetails"][unicode(self.styleSettings["styleName"])]["desktopTheme"])
                configPlasmaRc.sync()

                configPlasmaApplet = KConfig("plasma-desktop-appletsrc")
                group = configPlasmaApplet.group("Containments")
                for each in list(group.groupList()):
                    subgroup = group.group(each)
                    subcomponent = subgroup.readEntry('plugin')
                    if subcomponent == 'panel':
                        #print subcomponent
                        subgroup.writeEntry('location', self.styleSettings["styleDetails"][unicode(self.styleSettings["styleName"])]["panelPosition"])

                configPlasmaApplet.sync()

                configKwinRc = KConfig("kwinrc")
                groupWindowDecoration = configKwinRc.group("Style")
                groupWindowDecoration.writeEntry("PluginLib", self.styleSettings["styleDetails"][unicode(self.styleSettings["styleName"])]["windowDecoration"])
                configKwinRc.sync()

            session = dbus.SessionBus()

            try:
                proxy = session.get_object('org.kde.kwin', '/KWin')
                proxy.reconfigure()
            except dbus.DBusException:
                pass

        # Spun Settings
        if self.packageSettings["hasChanged"]:
            spun = SpunRC()
            if spun.isEnabled():
                rootActions += "disable_spun "
            else:
                rootActions += "enable_spun "

        # Services Settings
        if self.servicesSettings["hasChanged"]:
            if self.servicesSettings["enableCups"] and not self.daemon.isEnabled("cups"):
                rootActions += "enable_cups "
            elif not self.servicesSettings["enableCups"] and self.daemon.isEnabled("cups"):
                rootActions += "disable_cups "
            if self.servicesSettings["enableBluetooth"] and not self.daemon.isEnabled("bluetooth"):
                rootActions += "enable_blue "
            elif not self.servicesSettings["enableBluetooth"] and self.daemon.isEnabled("bluetooth"):
                rootActions += "disable_blue "

        # Security Settings
        if self.securitySettings["hasChanged"]:
            if self.securitySettings["enableClam"] and not self.daemon.isEnabled("clamd"):
                rootActions += "enable_clam "
            elif not self.securitySettings["enableClam"] and self.daemon.isEnabled("clamd"):
                rootActions += "disable_clam "
            if self.securitySettings["enableFire"] and not self.daemon.isEnabled("ufw"):
                rootActions += "enable_fire "
            elif not self.securitySettings["enableFire"] and self.daemon.isEnabled("ufw"):
                rootActions += "disable_fire "

        if hasChanged:
            self.killPlasma()

        if not rootActions == "":
            os.system("kdesu konsole -e kapudan-rootactions " + rootActions)

        return True

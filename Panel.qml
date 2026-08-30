import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "harshith.jarvis-hud"
  ipcTarget: "harshith.jarvis-hud.panel"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  readonly property var barIdentity: hostWidget || root

  readonly property string scriptPath:
    Qt.resolvedUrl("jarvis-engine.sh").toString().replace(/^file:\/\//, "")

  property string status: "ONLINE"
  property string protocol: "NOMINAL"
  property int cpuUsage: 12
  property int cpuTemp: 60
  property int cpuCores: 20
  property string gpuName: "NVIDIA RTX 4060"
  property int gpuLoad: 0
  property int gpuTemp: 46
  property int gpuVramUsed: 3898
  property int gpuVramTotal: 8188
  property int gpuVramPct: 47
  property string memUsed: "10.9"
  property string memTotal: "15.2"
  property int memPct: 71
  property int batPct: 56
  property string batStatus: "Charging"
  property string uptime: "23 hours"
  property string hostname: "omarchy"

  readonly property color fg: bar ? bar.foreground : Color.popups.text
  readonly property color bg: Color.popups.background
  readonly property color accent: Color.accent
  readonly property string fontFam: bar ? bar.fontFamily : Style.font.family

  function open() {
    root.controller.show()
    root.refresh()
  }

  function close() {
    root.controller.hide()
  }

  function toggle() {
    if (root.opened) root.close()
    else root.open()
  }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.hostWidget || root, direction)
    return false
  }

  function refresh() {
    stateProc.command = ["bash", scriptPath, "telemetry"]
    stateProc.running = true
  }

  function triggerProtocol(name) {
    actionProc.command = ["bash", scriptPath, name]
    actionProc.running = true
  }

  Process {
    id: stateProc
    running: false
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var data = JSON.parse(text)
          if (data.status) root.status = data.status
          if (data.protocol) root.protocol = data.protocol
          if (data.cpu) {
            root.cpuUsage = data.cpu.usage || 0
            root.cpuTemp = data.cpu.temp || 0
            root.cpuCores = data.cpu.cores || 8
          }
          if (data.gpu) {
            root.gpuName = data.gpu.name || "GPU"
            root.gpuLoad = data.gpu.load || 0
            root.gpuTemp = data.gpu.temp || 0
            root.gpuVramUsed = data.gpu.vram_used_mb || 0
            root.gpuVramTotal = data.gpu.vram_total_mb || 0
            root.gpuVramPct = data.gpu.vram_pct || 0
          }
          if (data.memory) {
            root.memUsed = data.memory.used_gb || "0"
            root.memTotal = data.memory.total_gb || "0"
            root.memPct = data.memory.pct || 0
          }
          if (data.power) {
            root.batPct = data.power.battery_pct || 100
            root.batStatus = data.power.status || ""
          }
          if (data.system) {
            root.uptime = data.system.uptime || ""
            root.hostname = data.system.hostname || ""
          }
        } catch(e) {}
      }
    }
  }

  Process {
    id: actionProc
    running: false
    onExited: root.refresh()
  }

  Timer {
    interval: 3000
    running: root.opened
    repeat: true
    onTriggered: root.refresh()
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.hostWidget || root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(400))
    contentHeight: panel.fittedContentHeight(panelColumn.implicitHeight, Style.space(560))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
    }

    ScrollView {
      id: scrollArea
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.top: parent.top
      anchors.bottom: parent.bottom
      anchors.bottomMargin: -panel.padding
      clip: true
      ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
      ScrollBar.vertical.policy: panelColumn.implicitHeight > height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff

      Column {
        id: panelColumn
        width: scrollArea.availableWidth
        spacing: Style.space(12)

        // Hologram Arc Reactor Header
        Item {
          width: parent.width
          implicitHeight: coreIcon.implicitHeight

          Text {
            id: coreIcon
            textFormat: Text.PlainText
            text: "󰮯"
            color: root.accent
            font.family: root.fontFam
            font.pixelSize: Style.font.display
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
          }

          Column {
            anchors.left: coreIcon.right
            anchors.leftMargin: Style.space(14)
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: Style.space(2)

            Row {
              spacing: Style.space(6)
              Text {
                textFormat: Text.PlainText
                text: "JARVIS HUD"
                color: root.accent
                font.family: root.fontFam
                font.pixelSize: Style.font.title
                font.bold: true
              }
              Text {
                textFormat: Text.PlainText
                text: "[" + root.status + "]"
                color: "#38ef7d"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
              }
            }

            Text {
              textFormat: Text.PlainText
              text: root.hostname + " • " + root.uptime
              color: Qt.darker(root.fg, 1.4)
              font.family: root.fontFam
              font.pixelSize: Style.font.caption
            }
          }
        }

        PanelSeparator { width: parent.width }

        // CPU Diagnostics Box
        Column {
          width: parent.width
          spacing: Style.space(4)

          Item {
            width: parent.width
            implicitHeight: cpuLabel.implicitHeight

            Row {
              id: cpuLabel
              spacing: Style.space(6)
              Text { textFormat: Text.PlainText; text: "󰍛"; font.pixelSize: Style.font.caption; color: root.accent }
              Text {
                textFormat: Text.PlainText
                text: "CPU LOAD (" + root.cpuCores + " CORES)"
                color: root.fg
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
              }
            }

            Text {
              textFormat: Text.PlainText
              text: root.cpuUsage + "% • " + root.cpuTemp + "°C"
              color: root.accent
              font.family: root.fontFam
              font.pixelSize: Style.font.caption
              font.bold: true
              anchors.right: parent.right
            }
          }

          Rectangle {
            width: parent.width
            height: Style.space(6)
            radius: Style.space(3)
            color: Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.1)

            Rectangle {
              height: parent.height
              width: Math.min(parent.width, Math.max(0, parent.width * (root.cpuUsage / 100)))
              radius: Style.space(3)
              color: root.cpuUsage > 80 ? "#ff4d4d" : root.accent
            }
          }
        }

        // NVIDIA GPU Diagnostics Box
        Column {
          width: parent.width
          spacing: Style.space(4)

          Item {
            width: parent.width
            implicitHeight: gpuLabel.implicitHeight

            Row {
              id: gpuLabel
              spacing: Style.space(6)
              Text { textFormat: Text.PlainText; text: "󰢮"; font.pixelSize: Style.font.caption; color: "#76b900" }
              Text {
                textFormat: Text.PlainText
                text: "NVIDIA RTX 4060 VRAM"
                color: root.fg
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
              }
            }

            Text {
              textFormat: Text.PlainText
              text: (root.gpuVramUsed / 1024).toFixed(1) + " / " + (root.gpuVramTotal / 1024).toFixed(1) + " GB • " + root.gpuTemp + "°C"
              color: "#76b900"
              font.family: root.fontFam
              font.pixelSize: Style.font.caption
              font.bold: true
              anchors.right: parent.right
            }
          }

          Rectangle {
            width: parent.width
            height: Style.space(6)
            radius: Style.space(3)
            color: Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.1)

            Rectangle {
              height: parent.height
              width: Math.min(parent.width, Math.max(0, parent.width * (root.gpuVramPct / 100)))
              radius: Style.space(3)
              color: "#76b900"
            }
          }
        }

        // RAM & Battery Dual Tiles
        Row {
          width: parent.width
          spacing: Style.space(8)

          Rectangle {
            width: (parent.width - Style.space(8)) / 2
            height: Style.space(44)
            radius: Style.space(6)
            color: Qt.rgba(0.2, 0.6, 1.0, 0.1)
            border.color: Qt.rgba(0.2, 0.6, 1.0, 0.25)
            border.width: 1

            Column {
              anchors.centerIn: parent
              spacing: 2
              Text {
                textFormat: Text.PlainText
                text: "RAM MEMORY"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                color: Qt.darker(root.fg, 1.4)
              }
              Text {
                textFormat: Text.PlainText
                text: root.memUsed + " / " + root.memTotal + " GB (" + root.memPct + "%)"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
                color: "#11998e"
              }
            }
          }

          Rectangle {
            width: (parent.width - Style.space(8)) / 2
            height: Style.space(44)
            radius: Style.space(6)
            color: Qt.rgba(0.2, 0.8, 0.4, 0.1)
            border.color: Qt.rgba(0.2, 0.8, 0.4, 0.25)
            border.width: 1

            Column {
              anchors.centerIn: parent
              spacing: 2
              Text {
                textFormat: Text.PlainText
                text: "BATTERY / POWER"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                color: Qt.darker(root.fg, 1.4)
              }
              Text {
                textFormat: Text.PlainText
                text: root.batPct + "% • " + root.batStatus
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
                color: "#38ef7d"
              }
            }
          }
        }

        PanelSeparator { width: parent.width }

        PanelSectionHeader { text: "Tactical Protocols" }

        // Protocol Action Buttons
        Row {
          width: parent.width
          spacing: Style.space(6)

          Rectangle {
            width: (parent.width - Style.space(12)) / 3
            height: Style.space(36)
            radius: Style.space(6)
            color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.15)
            border.color: root.accent
            border.width: 1

            Row {
              anchors.centerIn: parent
              spacing: 4
              Text { textFormat: Text.PlainText; text: "⚡"; font.pixelSize: Style.font.caption }
              Text {
                textFormat: Text.PlainText
                text: "Overdrive"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
                color: root.accent
              }
            }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: root.triggerProtocol("overdrive")
            }
          }

          Rectangle {
            width: (parent.width - Style.space(12)) / 3
            height: Style.space(36)
            radius: Style.space(6)
            color: Qt.rgba(0.2, 0.8, 0.4, 0.15)
            border.color: "#38ef7d"
            border.width: 1

            Row {
              anchors.centerIn: parent
              spacing: 4
              Text { textFormat: Text.PlainText; text: "🍃"; font.pixelSize: Style.font.caption }
              Text {
                textFormat: Text.PlainText
                text: "Stealth"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
                color: "#38ef7d"
              }
            }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: root.triggerProtocol("eco")
            }
          }

          Rectangle {
            width: (parent.width - Style.space(12)) / 3
            height: Style.space(36)
            radius: Style.space(6)
            color: Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.1)
            border.color: Qt.darker(root.fg, 1.5)
            border.width: 1

            Row {
              anchors.centerIn: parent
              spacing: 4
              Text { textFormat: Text.PlainText; text: "🧹"; font.pixelSize: Style.font.caption }
              Text {
                textFormat: Text.PlainText
                text: "Purge"
                font.family: root.fontFam
                font.pixelSize: Style.font.caption
                font.bold: true
                color: root.fg
              }
            }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: root.triggerProtocol("purge")
            }
          }
        }
      }
    }
  }
}

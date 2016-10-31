#Author-Peter Böker
#Description-Simple Add-In to create HTD, AT and T timing belt wheels.

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import json


# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

app = adsk.core.Application.get()
ui = app.userInterface
cmdId = "TimingBeltWheelAddInMenuEntry"
cmdName = "Timing belt wheel"
dialogTitle = "Create Timing belt wheel"
cmdDesc = "Create HTD, AT and T timing belt wheels."
cmdRes = ".//ressources//TimingBeltWheelCreator"

class TwcCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
	global cmdId
	global ui
	def __init__(self):
		super().__init__()

	def updateWheelType(self, listItems, selectedType):
		types = ["HTD 3", "HTD 5", "HTD 8", "HTD 14", "AT"]
		for t in types:
			if t == selectedType:
				selected = True
			else:
				selected = False
			listItems.add(t, selected)

	def notify(self, args):
		product = app.activeProduct
		design = adsk.fusion.Design.cast(product)
		defaultUnit = design.fusionUnitsManager.defaultLengthUnits
		lastPrefs = design.attributes.itemByName(cmdId, "lastUsedOptions")
		_wheelType = "HTD 5"
		_teeth = 32
		_wheelThickness = adsk.core.ValueInput.createByReal(2.0)
		if lastPrefs:
			try:
				lastPrefs = json.loads(lastPrefs.value)
				_wheelType = lastPrefs.get('wheelType', _wheelType)
				_teeth = lastPrefs.get('teeth', _teeth)
				_wheelThickness = adsk.core.ValueInput.createByReal(lastPrefs.get('wheelThickness', _wheelThickness))
			except:
				ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
				return

		eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
		cmd = eventArgs.command
		inputs = cmd.commandInputs
		wheelType = inputs.addDropDownCommandInput(cmdId + "_wheelType", "Wheel type", 1)
		wheelType.tooltip = "Choose the type of wheel you want to create."
		self.updateWheelType(wheelType.listItems, _wheelType)

		teeth = inputs.addIntegerSpinnerCommandInput(cmdId + "_teeth", "Teeth", 10, 500, 1, _teeth)
		teeth.tooltip = "Defines the number of teeth the wheel will have."

		wheelThickness = inputs.addValueInput(cmdId + "_wheelThickness", "Wheel width", defaultUnit, _wheelThickness)
		wheelThickness.tooltip = "Defines the thickness of the wheel"

		# Connect to the execute event.
		onExecute = TwcCommandExecuteHandler()
		cmd.execute.add(onExecute)
		handlers.append(onExecute)

		onInputChanged = TwcCommandInputChangedHandler()
		cmd.inputChanged.add(onInputChanged)
		handlers.append(onInputChanged)


class TwcCommandExecuteHandler(adsk.core.CommandEventHandler):
	global cmdId
	def __init__(self):
		super().__init__()

	def getPrefsObject(self, inputs):
		obj = {
			"wheelType": inputs.itemById(cmdId + "_wheelType").selectedItem.name,
			"teeth": inputs.itemById(cmdId + "_teeth").value,
			"wheelThickness": inputs.itemById(cmdId + "_wheelThickness").value
		}
		return obj

	def notify(self, args):
		global app
		global ui
		global dialogTitle
		global cmdId

		product = app.activeProduct
		design = adsk.fusion.Design.cast(product)
		eventArgs = adsk.core.CommandEventArgs.cast(args)
		inputs = eventArgs.command.commandInputs
		try:
			prefs = self.getPrefsObject(inputs)

			# Save last choosed options
			design.attributes.add(cmdId, "lastUsedOptions", json.dumps(prefs))
		except:
			if ui:
				ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class TwcCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
	def __init__(self):
		super().__init__()

	def notify(self, args):
		global ui
		global cmdId
		command = args.firingEvent.sender
		inputs = command.commandInputs


def run(context):
	try:
		global ui
		global cmdId
		global dialogTitle
		global cmdDesc
		global cmdRes
		# Get the CommandDefinitions collection.
		cmdDefs = ui.commandDefinitions

		twcButton = cmdDefs.addButtonDefinition(cmdId, dialogTitle, cmdDesc, cmdRes)

		# Connect to the command created event.
		commandCreated = TwcCommandCreatedEventHandler()
		twcButton.commandCreated.add(commandCreated)
		handlers.append(commandCreated)

		# Get the Create panel in the model workspace.
		toolbarPanel = ui.allToolbarPanels.itemById("SolidCreatePanel")

		# Add the button to the bottom of the panel.
		buttonControl = toolbarPanel.controls.addCommand(twcButton, "", False)
		buttonControl.isVisible = True
	except:
		if ui:
			ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
	try:
		global app
		global ui
		global cmdId
		# Clean up the UI.
		cmdDef = ui.commandDefinitions.itemById(cmdId)
		if cmdDef:
			cmdDef.deleteMe()

		toolbarPanel = ui.allToolbarPanels.itemById("SolidCreatePanel")
		cntrl = toolbarPanel.controls.itemById(cmdId)
		if cntrl:
			cntrl.deleteMe()
	except:
		if ui:
			ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

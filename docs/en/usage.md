# Using Paint

<style>
thead tr th:first-child, tbody tr td:first-child {
  min-width: 30%;
}
</style>

## Starting **Paint**

Select the **Paint** icon from the application list; the application filename is “esrille-paint”:

![Paint icon](../icon.png)

<br>
A **Paint** window like below will open:

![The main screen layout](layout.png)

When you move your mouse cursor over the drawing canvas, it becomes a cross-hair cursor.
To draw a curved line, click and drag your mouse on the canvas.
Use the [**Colors**] button to choose a color for your drawing.
Click the [**Tools**] button to access different drawing tools.
We will describe each tool in the upcoming sections.

<br>
To run **Paint** from the command line, type as follow:

```
$ esrille-paint [filename]...
```

In the filename part, type the name of the file you want to open.
When creating a new file, you do not have to specify the filename.

## Colors

To select a color, click the [Colors] button, and a “Pick a Color” dialog will open:

![Pick a Color](color.png)

To change the current color, click on the desired color in the pallet, and click [Select].
If you want to create a custom color, click the [+] button within the dialog.

## Tools

To select a tool, click the [Tools] button, and a “Tool” dialog will open:

![Tool](tool.png)

To change the current tool, click on the desired tool within the dialog.

Frequently used tools can be selected using keyboard shortcuts.
Simply type the key corresponding to the tool listed in the table below:

Tool | Shortcut | Description
---|---|---
![Lasso](../figures/lasso-symbolic.svg) Lasso | | Create a non-rectangular selection to move, stretch or shrink.<br>Drag in the canvas to select a non-rectangular area. Then position the mouse cursor inside the area surrounded by a dotted outline and drag.<br>• Use the [Shift] key to constrain the movement and/or to maintain the proportion of your selection.<br>• Use the [Escape] key to complete the current selection.
![Select](../figures/selection-symbolic.svg) Select | <b>S</b> | Create a rectangular selection to move, stretch or shrink. Drag in the canvas to select a rectangular area. Then position the mouse cursor inside the area surrounded by a dotted outline and drag.<br>• Use the [Shift] key to constrain the movement and/or to maintain the proportion of your selection.<br>• Use the [Escape] key to complete the current selection.<br>• Use [Ctrl]+[A] to select the entire drawing canvas.
![Pencil](../figures/pencil-symbolic.svg) Pencil | <b>P</b> | Draw a curved line where you drag.
![Eraser](../figures/eraser-symbolic.svg) Eraser | <b>E</b> | Erase where you drag.
![Line](../figures/line-symbolic.svg) Line | | Draw a straight line as you drag. The drawing is completed when you finish dragging.<br>• Use the [Shift] key to constrain drawing.
![Rectangle](../figures/rectangle-symbolic.svg) Rectangle | | Draw a rectangle as you drag. The drawing is completed when you finish dragging.<br>• Use the [Shift] key to draw squares.
![Oval](../figures/oval-symbolic.svg) Oval | | Draw an oval as you drag. The drawing is completed when you finish dragging.<br>• Use the [Shift] key to draw circles.
![Text](../figures/text-symbolic.svg) Text | <b>T</b> | Type text.<br>Click where you want to add text. Then type your text.<br>You can move, stretch or shrink the text; position the mouse cursor around the text and drag.<br>• Use the [Shift] key to constrain the movement and/or to maintain the proportion of the text.<br>• Use the [Escape] key to finish typing.
![Flood Fill](../figures/floodfill-symbolic.svg) Flood Fill | | Fill an outlined area.<br>Click in any outlined area you want to fill.

## Style

To select a line width, click the [Styles] button, and a “Style” dialog will open:

![Style](style.png)

Click any style to make it the current line width.

Style | Description
---|---
![1px](../figures/1px-symbolic.svg) &nbsp;&nbsp;&nbsp;&nbsp; | 1 px
![2px](../figures/2px-symbolic.svg) | 2 px
![4px](../figures/4px-symbolic.svg) | 4 px
![8px](../figures/8px-symbolic.svg) | 8 px

## Editing

You can use edit buttons to perform image editing tasks, such as Cut and Paste.

Button | Description
---|---
Undo<br><b>[Ctrl]+[Z]</b> | Undo the last action.
Redo<br><b>[Ctrl]+[Shift]+[Z]</b> | Redo the last action you undid.
Cut<br><b>[Ctrl]+[X]</b> | Remove the selection to the Clipboard.
Copy<br><b>[Ctrl]+[C]</b> | Copy the selection to  the Clipboard.
Paste<br><b>[Ctrl]+[V]</b> | Paste the image or text from the Clipboard. You can move, stretch or shrink the pasted content where you drag.<br>• Use the [Shift] key to constrain the movement and/or to maintain the proportion of the pasted image or text.

## Saving

Your changes to the image will be lost if you don't save them to a file.
To save changes, click the [Save] button in the header bar of the **Paint** window.
Enter a filename the first time you save a new image, then click the [Save] button in the dialog box.

You can also use <b>[Ctrl]+[S]</b> to save the image.

## Primary menu

You can open the primary menu with the [Primary menu] button in the header bar.
The primary menu contains the following menu items.

Menu item | Description
---|---
New...<br><b>[Ctrl]+[N]</b> | Enter the width and height of the new image, then click [OK] to open a new Paint window.
Open...<br><b>[Ctrl]+[O]</b> | Select the image file to open, then click [Open] to open a new Paint window.
Save<br><b>[Ctrl]+[S]</b> | Save changes.<br>Enter a filename the first time you save a new image, then click the [Save] button in the dialog box.
Save As... | Save a copy of the image.<br>Enter a filename for the copy, then click the [Save] button in the dialog box.
Font... | Change the font and font size used with the Text tool.
Transparent Mode | If checked, selection tools do not select pixels of the background color.
Anti-Aliased | If checked, draw smooth lines. To fill an outlined area completely, draw outlines without anti-aliasing.
Background Color | Choose the background color.
Help | Open the Paint's user guide in the default web browser.
About Paint | Open a dialog box that displays the Paint's version number and other information.

### Note

Paint currently supports the PNG file format only.
The other file formats will be supported in the future versions.

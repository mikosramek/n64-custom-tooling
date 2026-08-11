bl_info = {
    "name": "Custom N64 Tool Panel",
    "author": "Miko Sramek",
    "version":(0, 0, 1),
    "blender": (4, 5, 7),
    "location": "3D Viewport > Sidebar > CN64",
    "description": "Custom tools for working with N64 homebrewing",
    "category": "Development",
}

import bpy
from bpy.props import StringProperty
import re
from datetime import datetime
import math

class QueryProps(bpy.types.PropertyGroup):
    scene_name: StringProperty(default="scene")
    scene_folder: StringProperty(
        name="Template Folder",
        description="Path to Template Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')

class MESH_OT_export_game_objects(bpy.types.Operator):
    """Grabs the game objects and exports them as text or something"""
    
    bl_idname = "mesh.export_game_objects"
    bl_label = "Export game objects"
    
    sceneName: StringProperty(default="scene")
    sceneFolder: StringProperty(default="/Users/mikosramek/Documents/n64/pigeon-grabbing/scenes/")
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

        # Get all the templates into memory
        baseTemplate = ""
        with open(self.sceneFolder + "/templates/base_template.txt", 'r') as f:
            baseTemplate = f.read()

        actorTemplate = ""
        with open(self.sceneFolder + "/templates/actor_template.txt", 'r') as f:
            actorTemplate = f.read()

        modelImportTemplate = ""
        with open(self.sceneFolder + "/templates/model_import_template.txt", 'r') as f:
            modelImportTemplate = f.read()

        modelTemplate = ""
        with open(self.sceneFolder + "/templates/model_template.txt", 'r') as f:
            modelTemplate = f.read()
        
        # for each mesh found
        # name, location, scale, rot
        # keep a record of each unique name
        modelNames = set()
        actors = []

        NAME = self.sceneName
        LOWERCASE_NAME = self.sceneName.lower()
        UPPERCASE_NAME = self.sceneName.upper()
        DATE = datetime.now().strftime("%Y-%m-%d")

        baseTemplate = re.sub("<NAME>", NAME, baseTemplate)
        baseTemplate = re.sub("<LOWERCASE_NAME>", LOWERCASE_NAME, baseTemplate)
        baseTemplate = re.sub("<UPPERCASE_NAME>", UPPERCASE_NAME, baseTemplate)
        baseTemplate = re.sub("<DATE>", DATE, baseTemplate)

        ACTOR_COUNT = 0
        MODEL_COUNT = 0
        MODEL_IMPORT = ""
        MODELS = ""
        ACTORS = ""

        for obj in sel_objs:
            name = obj.name
            obj.rotation_mode = "XYZ"

            # Handle actors
            if "a_" in name:
                name = re.sub(r"a_(\w+)[\.]*\d*", r"\1", name)
                modelNames.add(name)

                # in Blender, Y/Z are swapped, so we swap them here for position and rotation
                position = f"{obj.location[0]}f * xPositionMultiplier, {obj.location[2]}f * yPositionMultiplier, {-obj.location[1]}f * zPositionMultiplier"

                rotation = f"{obj.rotation_euler[0]}f, {-obj.rotation_euler[2]}f, {-obj.rotation_euler[1]}f"
                scale = "{:f}f * scaleMultiplier, {:f}f * scaleMultiplier, {:f}f * scaleMultiplier".format(*obj.scale)
                actor = {
                    "model": name,
                    "position": "(float[3]){ " + position + " }",
                    "rotation": "(float[3]){ " + rotation + " }",
                    "scale": "(float[3]){ " + scale + "}"
                }
                actors.append(actor)
        
        ACTOR_COUNT = len(actors)
        MODEL_COUNT = len(modelNames)

        # ModelData <MODEL> = setupModel("rom:/<MODEL>.t3dm");
        # models[<INDEX>] = <MODEL>.model;
        for index, model in enumerate(modelNames):
            modelIndex = re.sub("<INDEX>", str(index), modelTemplate)
            modelImport = re.sub("<MODEL>", model, modelIndex)
            MODELS += "\t"+modelImport+"\n"

            MODEL_IMPORT += "\t"+re.sub("<MODEL>", model, modelImportTemplate) + "\n"
        
        for index, actor in enumerate(actors):
            addIndex = re.sub("<INDEX>", str(index), actorTemplate)
            addModel = re.sub("<MODEL>", actor["model"], addIndex)
            addPosition = re.sub("<POSITION>", actor["position"], addModel)
            addRotation = re.sub("<ROTATION>", actor["rotation"], addPosition)
            addScale = re.sub("<SCALE>", actor["scale"], addRotation)

            ACTORS += "\t"+addScale+"\n"

        baseTemplate = re.sub("<ACTOR_COUNT>", str(ACTOR_COUNT), baseTemplate)
        baseTemplate = re.sub("<MODEL_COUNT>", str(MODEL_COUNT), baseTemplate)

        baseTemplate = re.sub("<MODEL_IMPORT>", MODEL_IMPORT, baseTemplate)
        baseTemplate = re.sub("<MODELS>", MODELS, baseTemplate)
        baseTemplate = re.sub("<ACTORS>", ACTORS, baseTemplate)

        filename = self.sceneFolder + self.sceneName + ".txt"
        with open(filename, 'w+') as f:
            f.write(baseTemplate)
        return {"FINISHED"}

class VIEW3D_PT_game_export(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    bl_category = "CN64"
    bl_label = "Export Game Objects"
    
    def draw(self, context):
        props = bpy.context.scene.QueryProps

        row = self.layout.row()
        row.prop(props, "scene_folder", text="Scene Folder")
        row = self.layout.row()
        row.prop(props, "scene_name", text="Scene Name")
        
        row = self.layout.row()
        op = row.operator("mesh.export_game_objects", text="Export Game Object Data")
        op.sceneFolder = props.scene_folder
        op.sceneName = props.scene_name


def register():
    bpy.utils.register_class(QueryProps);
    bpy.utils.register_class(MESH_OT_export_game_objects);
    bpy.utils.register_class(VIEW3D_PT_game_export);
    bpy.types.Scene.QueryProps = bpy.props.PointerProperty(type=QueryProps)
    
def unregister():
    bpy.utils.unregister_class(QueryProps);
    bpy.utils.unregister_class(MESH_OT_export_game_objects);
    bpy.utils.unregister_class(VIEW3D_PT_game_export);
    del(bpy.types.Scene.QueryProps)
    
if __name__ == "__main__":
    register()
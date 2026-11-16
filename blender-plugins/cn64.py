bl_info = {
    "name": "Custom N64 Tool Panel",
    "author": "Miko Sramek",
    "version":(0, 0, 6),
    "blender": (4, 5, 7),
    "location": "3D Viewport > Sidebar > CN64",
    "description": "Custom tools for working with N64 homebrewing",
    "category": "Development",
}

import bpy
from bpy.props import StringProperty
from bpy.props import BoolProperty
import re
from datetime import datetime
import math

def trim(input):
    return round(input, 4)

def readTemplate(filepath):
    template = ""
    with open(filepath, 'r') as f:
        template = f.read()
        return template

def getSceneData(name):
    pattern = "scene_(\d\d)_(\w+)"
    match = re.search(pattern, name)
    scene = {
        "id": match.group(1),
        "name": match.group(2),
        "lowerName": match.group(2).lower(),
        "collectionName": name
    }
    return scene

def findSceneNames():
    scenesFound = []
    for collection in bpy.data.collections:
        print(collection.name)
        name = collection.name
        if name.startswith("scene_"):
            scenesFound.append(getSceneData(name))
    return scenesFound


class QueryProps(bpy.types.PropertyGroup):
    level_name: StringProperty(default="level")
    level_id: StringProperty(default="0")
    scene_folder: StringProperty(
        name="Template Folder",
        description="Path to Template Directory",
        default="/Users/mikosramek/Documents/n64/pigeon-grabbing/scenes/",
        maxlen=1024,
        subtype='DIR_PATH')
    collisionsVisible: BoolProperty(default=True)
    doorsVisible: BoolProperty(default=True)
    markersVisible: BoolProperty(default=True)

class MESH_OT_copy_rotation(bpy.types.Operator):
    bl_idname = "mesh.copy_rotation"
    bl_label = "Copies quaternion rotation from first to second selected objects"

    def execute(self, context):
        sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        if (len(sel_objs) == 2):
            if (sel_objs[0] == bpy.context.active_object):
                sel_objs[0].rotation_quaternion = sel_objs[1].rotation_quaternion
            else:
                sel_objs[1].rotation_quaternion = sel_objs[0].rotation_quaternion
        return {"FINISHED"}
class MESH_OT_copy_location(bpy.types.Operator):
    bl_idname = "mesh.copy_location"
    bl_label = "Copies location from first to second selected objects"

    def execute(self, context):
        sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        if (len(sel_objs) == 2):
            if (sel_objs[0] == bpy.context.active_object):
                sel_objs[0].location = sel_objs[1].location
            else:
                sel_objs[1].location = sel_objs[0].location
        return {"FINISHED"}

class MESH_OT_copy_scale(bpy.types.Operator):
    bl_idname = "mesh.copy_scale"
    bl_label = "Copies scale from first to second selected objects"

    def execute(self, context):
        sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        if (len(sel_objs) == 2):
            if (sel_objs[0] == bpy.context.active_object):
                sel_objs[0].scale = sel_objs[1].scale
            else:
                sel_objs[1].scale = sel_objs[0].scale
        return {"FINISHED"}

def exportLevel(levelName, levelId, sceneFolder):
    baseTemplate = readTemplate(sceneFolder + "/templates/level/base_template.txt")
    importTemplate = readTemplate(sceneFolder + "/templates/level/import_template.txt")
    loadTemplate = readTemplate(sceneFolder + "/templates/level/load_template.txt")
    unloadTemplate = readTemplate(sceneFolder + "/templates/level/unload_template.txt")
    registerTemplate = readTemplate(sceneFolder + "/templates/level/register_template.txt")

    NAME = levelName
    LOWERCASE_NAME = levelName.lower()

    baseTemplate = re.sub("<LEVEL_NAME>", NAME, baseTemplate)
    baseTemplate = re.sub("<LEVEL_NAME_LOWERCASE>", LOWERCASE_NAME, baseTemplate)
    baseTemplate = re.sub("<ID>", levelId, baseTemplate)

    scenes = findSceneNames()

    # <IMPORTS>
    # #include "../scenes/<SCENE>.h"
    IMPORTS = ""
    for index, scene in enumerate(scenes):
        IMPORTS += re.sub("<SCENE>", scene["lowerName"], importTemplate) + "\n"

    baseTemplate = re.sub("<IMPORTS>", IMPORTS, baseTemplate)
    # <FEATHER_COUNT>
    feather_count = 0;
    all_objects = list(bpy.data.objects)
    for obj in bpy.data.objects:
        if obj.name.startswith("e_feather"):
            feather_count += 1

    baseTemplate = re.sub("<FEATHER_COUNT>", str(feather_count), baseTemplate)

    # <REGISTER>
    # <LEVEL_NAME>Level.scenes[<INDEX>] = get<SCENE>();
    REGISTER = ""
    for index, scene in enumerate(scenes):
        NEW_REGISTER = registerTemplate
        NEW_REGISTER = re.sub("<LEVEL_NAME>", NAME, NEW_REGISTER)
        NEW_REGISTER = re.sub("<INDEX>", str(index), NEW_REGISTER)
        NEW_REGISTER = re.sub("<SCENE>", scene["name"], NEW_REGISTER)
        REGISTER += "\t" + NEW_REGISTER + "\n"
    
    baseTemplate = re.sub("<REGISTER>", REGISTER, baseTemplate)

    # <UNLOAD>
    # case <SCENE_ID>: rdpq_call_deferred(unload<SCENE_NAME>, NULL); break;
    UNLOAD = ""
    for index, scene in enumerate(scenes):
        NEW_UNLOAD = unloadTemplate
        NEW_UNLOAD = re.sub("<SCENE_ID>", scene["id"], NEW_UNLOAD)
        NEW_UNLOAD = re.sub("<SCENE_NAME>", scene["name"], NEW_UNLOAD)
        UNLOAD += "\t\t\t" + NEW_UNLOAD + "\n"
    
    baseTemplate = re.sub("<UNLOAD>", UNLOAD, baseTemplate)

    # <LOAD>
    # case <SCENE_ID>: <LEVEL_NAME>Level.activeScene = create<SCENE_NAME>(); break;
    LOAD = ""
    for index, scene in enumerate(scenes):
        NEW_LOAD = loadTemplate
        NEW_LOAD = re.sub("<SCENE_ID>", scene["id"], NEW_LOAD)
        NEW_LOAD = re.sub("<LEVEL_NAME>", NAME, NEW_LOAD)
        NEW_LOAD = re.sub("<SCENE_NAME>", scene["name"], NEW_LOAD)
        LOAD += "\t\t" + NEW_LOAD + "\n"
    
    baseTemplate = re.sub("<LOAD>", LOAD, baseTemplate)


    # Write scene file
    filename = sceneFolder + LOWERCASE_NAME + "_level" + ".txt"
    with open(filename, 'w+') as f:
        f.write(baseTemplate)

def exportScene(sceneName, levelId, sceneFolder):
    sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

    # Get all the templates into memory
    baseTemplate = readTemplate(sceneFolder + "/templates/base_template.txt")
    actorTemplate = readTemplate(sceneFolder + "/templates/actor_template.txt")
    entityTemplate = readTemplate(sceneFolder + "/templates/entity_template.txt")
    entityImportTemplate = readTemplate(sceneFolder + "/templates/entity_import_template.txt")
    modelImportTemplate = readTemplate(sceneFolder + "/templates/model_import_template.txt")
    modelTemplate = readTemplate(sceneFolder + "/templates/model_template.txt")
    doorTemplate = readTemplate(sceneFolder + "/templates/door_template.txt")
    spawnTemplate = readTemplate(sceneFolder + "/templates/spawn_template.txt")
    floorTemplate = readTemplate(sceneFolder + "/templates/floor_template.txt")
    colliderTemplate = readTemplate(sceneFolder + "/templates/collider_template.txt")
    
    # * arrays that contain the numbers / data
    # for each mesh found
    # name, location, scale, rot
    # keep a record of each unique name
    modelNames = set()
    entityNames = set()
    actors = []
    entities = []
    doors = []
    spawns = []
    floors = []
    colliders = []

    NAME = sceneName
    ID = levelId
    LOWERCASE_NAME = sceneName.lower()
    UPPERCASE_NAME = sceneName.upper()
    CAMELCASE_NAME = sceneName[0].lower() + sceneName[1:]
    DATE = datetime.now().strftime("%Y-%m-%d")

    baseTemplate = re.sub("<NAME>", NAME, baseTemplate)
    baseTemplate = re.sub("<CAMELCASE_NAME>", CAMELCASE_NAME, baseTemplate)
    baseTemplate = re.sub("<LOWERCASE_NAME>", LOWERCASE_NAME, baseTemplate)
    baseTemplate = re.sub("<UPPERCASE_NAME>", UPPERCASE_NAME, baseTemplate)
    baseTemplate = re.sub("<DATE>", DATE, baseTemplate)

    # * strings that get injected into templates
    ACTOR_COUNT = 0
    MODEL_COUNT = 0
    ENTITY_COUNT = 0
    DOOR_COUNT = 0
    SPAWN_COUNT = 0
    FLOOR_COUNT = 0
    COLLIDER_COUNT = 0
    MODEL_IMPORT = ""
    MODELS = ""
    ACTORS = ""
    ENTITY_ACTORS = ""
    ENTITY_IMPORTS = ""
    ENTITIES = ""
    DOORS = ""
    SPAWNS = ""
    FLOORS = ""
    COLLIDERS = ""

    def getPosition(obj):
        # in Blender, Y/Z are swapped, so we swap them here for position and rotation
        return f"{trim(obj.location[0])}f * xPositionMultiplier, {trim(obj.location[2])}f * yPositionMultiplier, {trim(-obj.location[1])}f * zPositionMultiplier"
    
    def getRotation(obj):
        # WXYZ
        return f"{trim(obj.rotation_quaternion[1])}f, {trim(obj.rotation_quaternion[3])}f, {-obj.rotation_quaternion[2]}f, {trim(obj.rotation_quaternion[0])}f"
    
    def getScale(obj):
        return f"{trim(obj.scale[0])}f * scaleMultiplier, {trim(obj.scale[1])}f * scaleMultiplier, {trim(obj.scale[2])}f * scaleMultiplier"

    def getActor(obj, name):
        # in Blender, Y/Z are swapped, so we swap them here for position and rotation

        skip = "false"
        if name.startswith("s_"):
            skip = "true"
            name = re.sub(r"^s_(\w+)", r"\1", name)
        
        skip_culling = "false"
        if name.startswith("sc_"):
            name = re.sub(r"^sc_(\w+)", r"\1", name)
            skip_culling = "true"
        
        actor = {
            "model": name,
            "position": "(float[3]){ " + getPosition(obj) + " }",
            "rotation": "(float[4]){ " + getRotation(obj) + " }",
            "scale": "(float[3]){ " + getScale(obj) + "}",
            "skip": skip,
            "skip_culling": skip_culling
        }
        return actor

    # Gather data for each object type
    for obj in sel_objs:
        name = obj.name
        obj.rotation_mode = "QUATERNION"
        

        # Handle actors
        if name.startswith("a_"):
            name = re.sub(r"a_(\w+)[\.]*\d*", r"\1", name)
            actor = getActor(obj, name)
            modelNames.add(actor["model"])
            actors.append(actor)

        if name.startswith("e_"):
            name = re.sub(r"e_(\w+)[\.]*\d*", r"\1", name)
            actor = getActor(obj, name)
            actor["id"] = obj["id"]
            modelNames.add(actor["model"])
            entityNames.add(actor["model"])
            entities.append(actor)
        
        if name.startswith("d_"):
            name = re.sub(r"d_(\w+)[\.]*\d*", r"\1", name)
            door = {
                "MIN_X": f"({trim(obj.location[0])}f * xPositionMultiplier) - ({trim(obj.scale[0])}f * xPositionMultiplier)",
                "MAX_X": f"({trim(obj.location[0])}f * xPositionMultiplier) + ({trim(obj.scale[0])}f * xPositionMultiplier)",
                "MIN_Z": f"({trim(-obj.location[1])}f * zPositionMultiplier) - ({trim(obj.scale[1])}f * zPositionMultiplier)",
                "MAX_Z": f"({trim(-obj.location[1])}f * zPositionMultiplier) + ({trim(obj.scale[1])}f * zPositionMultiplier)",
            }
            door["target_scene_id"] = obj["target_scene_id"]
            door["target_spawn_id"] = obj["target_spawn_id"]
            doors.append(door)

        if name.startswith("sp_"):
            name = re.sub(r"sp_(\w+)[\.]*\d*", r"\1", name)
            # z angle to x/y
            # x = cos(angle)
            # z = sin(angle)
            zAngle = obj.rotation_quaternion[3]
            spawnPoint = {
                "position": f"{trim(obj.location[0])}f * xPositionMultiplier, -0, {trim(-obj.location[1])}f * zPositionMultiplier",
                "rotation": f"{trim(obj.rotation_quaternion[3])}"
            }
            spawnPoint["id"] = obj["id"]
            spawns.append(spawnPoint)

        if name.startswith("floor_"):
            # name = re.sub(r"floor_(\w+)[\.]*\d*", r"\1", name)
            floor = {
                "POS_Y": trim(obj.location[2] + (obj.scale[2] * 2)),
                "POS_X": trim(obj.location[0]),
                "POS_Z": trim(obj.location[1]),
                "SCALE_X": trim(obj.scale[0]),
                "SCALE_Z": trim(obj.scale[1])
            }
            floors.append(floor)
        
        if name.startswith("aabb_"):
            # name = re.sub(r"aabb_(\w+)[\.]*\d*", r"\1", name)
            collider = {
                "TYPE": "COLLIDER_AABB",
                "POS_X": trim(obj.location[0]),
                "POS_Z": trim(-obj.location[1]),
                "SCALE_X": trim(obj.scale[0]),
                "SCALE_Z": trim(obj.scale[1]),
                "POSITION": "{ " + getPosition(obj) + " }",
                "ROTATION": "{ " + getRotation(obj) + " }",
                "SCALE": "{ " + getScale(obj) + " }"
            }
            colliders.append(collider)
        
        if name.startswith("obb_"):
            # name = re.sub(r"obb_(\w+)[\.]*\d*", r"\1", name)
            collider = {
                "TYPE": "COLLIDER_OBB",
                "POS_X": trim(obj.location[0]),
                "POS_Z": trim(-obj.location[1]),
                "SCALE_X": trim(obj.scale[0]),
                "SCALE_Z": trim(obj.scale[1]),
                "POSITION": "{ " + getPosition(obj) + " }",
                "ROTATION": "{ " + getRotation(obj) + " }",
                "SCALE": "{ " + f"{trim(obj.scale[0])}f * xPositionMultiplier, {trim(obj.scale[2])}f * yPositionMultiplier, {trim(obj.scale[1])}f * zPositionMultiplier" + " }"
            }
            colliders.append(collider)


    
    MODEL_COUNT = len(modelNames)
    ACTOR_COUNT = len(actors)
    ENTITY_COUNT = len(entities)
    DOOR_COUNT = len(doors)
    SPAWN_COUNT = len(spawns)
    FLOOR_COUNT = len(floors)
    COLLIDER_COUNT = len(colliders)

    # Create strings for replacement
    ## ModelData <MODEL> = setupModel("rom:/<MODEL>.t3dm");
    ## models[<INDEX>] = <MODEL>.model;
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
        addSkip = re.sub("<SKIP>", actor["skip"], addScale)
        addSkipCulling = re.sub("<SKIP_CULLING>", actor["skip_culling"], addSkip)

        ACTORS += "\t"+addSkipCulling+"\n"
    
    entityActorIndices = []
    for index, actor in enumerate(entities):
        adjustedIndex = index + ACTOR_COUNT
        entityActorIndices.append(adjustedIndex)

        addIndex = re.sub("<INDEX>", str(adjustedIndex), actorTemplate)
        addModel = re.sub("<MODEL>", actor["model"], addIndex)
        addPosition = re.sub("<POSITION>", actor["position"], addModel)
        addRotation = re.sub("<ROTATION>", actor["rotation"], addPosition)
        addScale = re.sub("<SCALE>", actor["scale"], addRotation)
        addSkip = re.sub("<SKIP>", actor["skip"], addScale)
        addSkipCulling = re.sub("<SKIP_CULLING>", actor["skip_culling"], addSkip)

        ENTITY_ACTORS += "\t"+addSkipCulling+"\n"
    
    ## #include "../entities/<ENTITY>.h"
    for index, entity in enumerate(entityNames):
        ENTITY_IMPORTS += re.sub("<ENTITY>", entity, entityImportTemplate) + "\n"

    for index, entity in enumerate(entities):
        # entities[<INDEX>] = create<ENTITY>(&actors[<ACTOR_INDEX>]);
        newEntity = re.sub("<INDEX>", str(index), entityTemplate)
        newEntity = re.sub("<ENTITY>", entity["model"], newEntity)
        newEntity = re.sub("<ID>", str(entity["id"]), newEntity)
        newEntity = re.sub("<ACTOR_INDEX>", str(entityActorIndices[index]), newEntity)
        
        ENTITIES += "\t"+newEntity+"\n"

    for index, door in enumerate(doors):
        newDoor = doorTemplate
        newDoor = re.sub("<INDEX>", str(index), newDoor)
        newDoor = re.sub("<TARGET_SPAWN_ID>", str(door["target_spawn_id"]), newDoor)
        newDoor = re.sub("<TARGET_SCENE_ID>", str(door["target_scene_id"]), newDoor)
        newDoor = re.sub("<MIN_X>", str(door["MIN_X"]), newDoor)
        newDoor = re.sub("<MAX_X>", str(door["MAX_X"]), newDoor)
        newDoor = re.sub("<MIN_Z>", str(door["MIN_Z"]), newDoor)
        newDoor = re.sub("<MAX_Z>", str(door["MAX_Z"]), newDoor)
        DOORS += newDoor + "\n"

    for index, spawn in enumerate(spawns):
        newSpawn = spawnTemplate
        newSpawn = re.sub("<INDEX>", str(index), newSpawn)
        newSpawn = re.sub("<SPAWN_ID>", str(spawn["id"]), newSpawn)
        newSpawn = re.sub("<SPAWN_ANGLE>", spawn["rotation"], newSpawn)
        newSpawn = re.sub("<SPAWN_POSITION>", spawn["position"], newSpawn)
        SPAWNS += newSpawn + "\n"
    
    for index, floor in enumerate(floors):
        newFloor = floorTemplate
        newFloor = re.sub("<INDEX>", str(index), newFloor)
        newFloor = re.sub("<POS_Y>", str(floor["POS_Y"]), newFloor)
        newFloor = re.sub("<POS_X>", str(floor["POS_X"]), newFloor)
        newFloor = re.sub("<POS_Z>", str(floor["POS_Z"]), newFloor)
        newFloor = re.sub("<SCALE_X>", str(floor["SCALE_X"]), newFloor)
        newFloor = re.sub("<SCALE_Z>", str(floor["SCALE_Z"]), newFloor)
        FLOORS += newFloor + "\n"
    
    for index, collider in enumerate(colliders):
        newCollider = colliderTemplate
        newCollider = re.sub("<INDEX>", str(index), newCollider)
        newCollider = re.sub("<TYPE>", collider["TYPE"], newCollider)
        newCollider = re.sub("<POS_X>", str(collider["POS_X"]), newCollider)
        newCollider = re.sub("<POS_Z>", str(collider["POS_Z"]), newCollider)
        newCollider = re.sub("<SCALE_X>", str(collider["SCALE_X"]), newCollider)
        newCollider = re.sub("<SCALE_Z>", str(collider["SCALE_Z"]), newCollider)
        newCollider = re.sub("<POSITION>", collider["POSITION"], newCollider)
        newCollider = re.sub("<ROTATION>", collider["ROTATION"], newCollider)
        newCollider = re.sub("<SCALE>", collider["SCALE"], newCollider)
        COLLIDERS += newCollider + "\n"


    # Inject each string into the base template
    baseTemplate = re.sub("<ENTITY_IMPORTS>", ENTITY_IMPORTS, baseTemplate)

    baseTemplate = re.sub("<SCENE_ID>", ID, baseTemplate)
    baseTemplate = re.sub("<ACTOR_COUNT>", str(ACTOR_COUNT + ENTITY_COUNT), baseTemplate)
    baseTemplate = re.sub("<MODEL_COUNT>", str(MODEL_COUNT), baseTemplate)
    baseTemplate = re.sub("<ENTITY_COUNT>", str(ENTITY_COUNT), baseTemplate)
    baseTemplate = re.sub("<SPAWN_COUNT>", str(SPAWN_COUNT), baseTemplate)
    baseTemplate = re.sub("<DOOR_COUNT>", str(DOOR_COUNT), baseTemplate)
    baseTemplate = re.sub("<FLOOR_COUNT>", str(FLOOR_COUNT), baseTemplate)
    baseTemplate = re.sub("<COLLIDER_COUNT>", str(COLLIDER_COUNT), baseTemplate)

    baseTemplate = re.sub("<MODEL_IMPORT>", MODEL_IMPORT, baseTemplate)
    baseTemplate = re.sub("<MODELS>", MODELS, baseTemplate)
    baseTemplate = re.sub("<ACTORS>", ACTORS, baseTemplate)
    baseTemplate = re.sub("<ENTITY_ACTORS>", ENTITY_ACTORS, baseTemplate)
    baseTemplate = re.sub("<ENTITIES>", ENTITIES, baseTemplate)
    baseTemplate = re.sub("<SPAWNS>", SPAWNS, baseTemplate)
    baseTemplate = re.sub("<DOORS>", DOORS, baseTemplate)
    baseTemplate = re.sub("<FLOORS>", FLOORS, baseTemplate)
    baseTemplate = re.sub("<COLLIDERS>", COLLIDERS, baseTemplate)

    # Write scene file
    filename = sceneFolder + LOWERCASE_NAME + ".txt"
    with open(filename, 'w+') as f:
        f.write(baseTemplate)

class MESH_OT_export_game_objects(bpy.types.Operator):
    """Grabs the game objects and exports them as text or something"""
    
    bl_idname = "mesh.export_game_objects"
    bl_label = "Export game objects"
    
    levelName: StringProperty(default="level")
    levelId: StringProperty(default="0")
    sceneFolder: StringProperty(default="/Users/mikosramek/Documents/n64/pigeon-grabbing/scenes/")
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        exportScene(self.levelName, self.sceneName, self.sceneFolder)

        return {"FINISHED"}

class MESH_OT_export_level(bpy.types.Operator):
    bl_idname = "mesh.export_game_level"
    bl_label = "Export game level"
    levelName: StringProperty(default="level")
    levelId: StringProperty(default="0")
    sceneFolder: StringProperty(default="/Users/mikosramek/Documents/n64/pigeon-grabbing/scenes/")
    # gather all collection with `scene_` in their names, and use them to create a level file
    def execute(self, context):
        exportLevel(self.levelName, self.levelId, self.sceneFolder)
        return {"FINISHED"}

class MESH_OT_export_scene(bpy.types.Operator):
    bl_idname = "mesh.export_game_scene"
    bl_label = "Export game scene"
    levelName: StringProperty(default="level")
    levelId: StringProperty(default="0")
    sceneFolder: StringProperty(default="/Users/mikosramek/Documents/n64/pigeon-grabbing/scenes/")
    
    # check to see if selected object is a collection with `scene_` in the name, then run `MESH_OT_export_game_objects` on their children
    def execute(self, context):
        active_collection = bpy.context.collection
        if not active_collection.name.startswith("scene_"):
            return {"FINISHED"}
        
        scene = getSceneData(active_collection.name)

        for obj in active_collection.all_objects:
            obj.select_set(True)

        exportScene(scene["name"], scene["id"], self.sceneFolder)
        bpy.ops.object.select_all(action='DESELECT')
        return {"FINISHED"}

class MESH_OT_export_all(bpy.types.Operator):
    bl_idname = "mesh.export_game_level_and_scene"
    bl_label = "Toggle collision models"
    levelName: StringProperty(default="level")
    levelId: StringProperty(default="0")
    sceneFolder: StringProperty(default="/Users/mikosramek/Documents/n64/pigeon-grabbing/scenes/")
    # run `MESH_OT_export_level`
    # gather all collections with `scene_` in their names
    # select all of them, and run `MESH_OT_export_scene` passing in the scene name
    def execute(self, context):
        # export level
        exportLevel(self.levelName, self.levelId, self.sceneFolder)

        # go through each scene
        scenes = findSceneNames()

        for index, scene in enumerate(scenes):
            colName = scene["collectionName"]
            for obj in bpy.data.collections[colName].all_objects:
                obj.select_set(True)
            exportScene(scene["name"], scene["id"], self.sceneFolder)
            bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_all(action='DESELECT')

        return {"FINISHED"}

class MESH_OT_toggle_collisions(bpy.types.Operator):
    bl_idname = "mesh.toggle_collisions"
    bl_label = "Toggle collision models"
    visibility: BoolProperty(default=True)

    def execute(self, context):
        sel_objs = [obj for obj in context.scene.objects if obj.type == 'MESH' and (obj.name.startswith('aabb_') or obj.name.startswith('obb_'))]
        for obj in sel_objs:
            obj.hide_set(self.visibility)
        context.scene.QueryProps.collisionsVisible = not self.visibility

        return {"FINISHED"}

class MESH_OT_toggle_doors(bpy.types.Operator):
    bl_idname = "mesh.toggle_doors"
    bl_label = "Toggle door models"
    visibility: BoolProperty(default=True)

    def execute(self, context):
        sel_objs = [obj for obj in context.scene.objects if obj.type == 'MESH' and obj.name.startswith('d_')]
        for obj in sel_objs:
            obj.hide_set(self.visibility)
        context.scene.QueryProps.doorsVisible = not self.visibility
        return {"FINISHED"}

class MESH_OT_toggle_markers(bpy.types.Operator):
    bl_idname = "mesh.toggle_markers"
    bl_label = "Toggle marker models"
    visibility: BoolProperty(default=True)

    def execute(self, context):
        sel_objs = [obj for obj in context.scene.objects if obj.type == 'MESH' and (obj.name.startswith('sp_'))]
        for obj in sel_objs:
            obj.hide_set(self.visibility)
        context.scene.QueryProps.markersVisible = not self.visibility
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
        row.prop(props, "level_name", text="Level Name")
        row = self.layout.row()
        row.prop(props, "level_id", text="Level ID")
        
        row = self.layout.row()
        op = row.operator("mesh.export_game_objects", text="Export Game Object Data")
        op.sceneFolder = props.scene_folder
        op.levelName = props.level_name
        op.levelId = props.level_id
        self.layout.label(text="Export Game Data")
        row = self.layout.row()
        level = row.operator("mesh.export_game_level", text="Level")
        level.sceneFolder = props.scene_folder
        level.levelName = props.level_name
        level.levelId = props.level_id
        scene = row.operator("mesh.export_game_scene", text="Scene")
        scene.sceneFolder = props.scene_folder
        scene.levelName = props.level_name
        scene.levelId = props.level_id
        both = row.operator("mesh.export_game_level_and_scene", text="All")
        both.sceneFolder = props.scene_folder
        both.levelName = props.level_name
        both.levelId = props.level_id

        self.layout.label(text="Toggle Objects")
        row = self.layout.row()
        button = row.operator("mesh.toggle_collisions", text="Collisions")
        button.visibility = props.collisionsVisible
        button = row.operator("mesh.toggle_doors", text="Doors")
        button.visibility = props.doorsVisible
        button = row.operator("mesh.toggle_markers", text="Markers")
        button.visibility = props.markersVisible


        self.layout.label(text="Copy to active object")
        row = self.layout.row()
        row.operator("mesh.copy_rotation", text="Q-Rot")
        row.operator("mesh.copy_location", text="Location")
        row.operator("mesh.copy_scale", text="Scale")



def register():
    bpy.utils.register_class(QueryProps);
    bpy.utils.register_class(MESH_OT_copy_rotation);
    bpy.utils.register_class(MESH_OT_copy_location);
    bpy.utils.register_class(MESH_OT_copy_scale);
    bpy.utils.register_class(MESH_OT_export_game_objects);
    bpy.utils.register_class(MESH_OT_export_level);
    bpy.utils.register_class(MESH_OT_export_scene);
    bpy.utils.register_class(MESH_OT_export_all);
    bpy.utils.register_class(MESH_OT_toggle_collisions);
    bpy.utils.register_class(MESH_OT_toggle_doors);
    bpy.utils.register_class(MESH_OT_toggle_markers);
    bpy.utils.register_class(VIEW3D_PT_game_export);
    bpy.types.Scene.QueryProps = bpy.props.PointerProperty(type=QueryProps)
    
def unregister():
    bpy.utils.unregister_class(QueryProps);
    bpy.utils.unregister_class(MESH_OT_copy_rotation);
    bpy.utils.unregister_class(MESH_OT_copy_location);
    bpy.utils.unregister_class(MESH_OT_copy_scale);
    bpy.utils.unregister_class(MESH_OT_export_game_objects);
    bpy.utils.unregister_class(MESH_OT_export_level);
    bpy.utils.unregister_class(MESH_OT_export_scene);
    bpy.utils.unregister_class(MESH_OT_export_all);
    bpy.utils.unregister_class(MESH_OT_toggle_collisions);
    bpy.utils.unregister_class(MESH_OT_toggle_doors);
    bpy.utils.unregister_class(MESH_OT_toggle_markers);
    bpy.utils.unregister_class(VIEW3D_PT_game_export);
    del(bpy.types.Scene.QueryProps)
    
if __name__ == "__main__":
    register()
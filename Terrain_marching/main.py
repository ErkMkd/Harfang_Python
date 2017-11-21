# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                   Terrain marching

# ===========================================================

import harfang as hg
from math import radians, degrees
import json

class RenderRect:
    def __init__(self, plus):
        renderer = plus.GetRenderer()

        # create primitive index buffer
        data = hg.BinaryData()
        data.WriteInt16s([0, 1, 2, 0, 2, 3])

        self.indices = renderer.NewBuffer()
        renderer.CreateBuffer(self.indices, data, hg.GpuBufferIndex)

        # create primitive vertex buffer
        self.vertex_layout = hg.VertexLayout()
        self.vertex_layout.AddAttribute(hg.VertexPosition, 3, hg.VertexFloat)
        self.vertex_layout.AddAttribute(hg.VertexUV0, 2, hg.VertexUByte,
                                      True)  # UVs are sent as normalized 8 bit unsigned integer (range [0;255])

        data = hg.BinaryData()
        x, y = 1, 1
        data.WriteFloats([-x, -y, 0])
        data.WriteUInt8s([0, 0])

        data.WriteFloats([-x, y, 0])
        data.WriteUInt8s([0, 255])

        data.WriteFloats([x, y, 0])
        data.WriteUInt8s([255, 255])

        data.WriteFloats([x, -y, 0])
        data.WriteUInt8s([255, 0])

        self.vertex = renderer.NewBuffer()
        renderer.CreateBuffer(self.vertex, data, hg.GpuBufferVertex)

    def draw(self,plus):
        hg.DrawBuffers(plus.GetRenderer(), 6, self.indices, self.vertex, self.vertex_layout)


class RenderToTexture(RenderRect):
    def __init__(self,plus,resolution : hg.Vector2):
        RenderRect.__init__(self,plus)

        renderer = plus.GetRenderer()

        # Création des textures de rendu:
        self.texture_rendu_1 = renderer.NewTexture()
        renderer.CreateTexture(self.texture_rendu_1, int(resolution.x), int(resolution.y), hg.TextureRGBA8,
                               hg.TextureNoAA, hg.TextureDefault, False)
        self.texture_rendu_1_depth = renderer.NewTexture()
        renderer.CreateTexture(self.texture_rendu_1_depth, int(resolution.x), int(resolution.y), hg.TextureDepth,
                               hg.TextureNoAA, hg.TextureDefault, False)

        # Création des frameBuffer objects:
        self.fbo_rendu_1 = renderer.NewRenderTarget()
        renderer.CreateRenderTarget(self.fbo_rendu_1)
        renderer.SetRenderTargetColorTexture(self.fbo_rendu_1, self.texture_rendu_1)
        renderer.SetRenderTargetDepthTexture(self.fbo_rendu_1, self.texture_rendu_1_depth)

        self.projection_matrix_mem = None
        self.view_matrix_mem = None
        self.projection_matrix_ortho = None


    def begin_render(self, plus):
        renderer = plus.GetRenderer()

        renderer.SetWorldMatrix(hg.Matrix4.Identity)
        self.projection_matrix_mem = renderer.GetProjectionMatrix()
        self.view_matrix_mem = renderer.GetViewMatrix()

        self.projection_matrix_ortho = hg.ComputeOrthographicProjectionMatrix(1., 500., 2, hg.Vector2(1, 1))
        renderer.SetProjectionMatrix(self.projection_matrix_ortho)
        renderer.SetViewMatrix(hg.Matrix4.Identity)


    def end_render(self,plus):
        renderer = plus.GetRenderer()
        self.draw(plus)
        renderer.SetProjectionMatrix(self.projection_matrix_mem)
        renderer.SetViewMatrix(self.view_matrix_mem)


class TerrainMarching:
    def __init__(self, plus, scene):
        self.lumiere_soleil = scene.GetNode("Sun")
        self.lumiere_ciel = scene.GetNode("SkyLigth")

        self.couleur_horizon = hg.Color(255. / 255. * 0.75, 221. / 255. * 0.75, 199 / 255. * 0.75, 1.)
        # self.couleur_zenith=hg.Color(255/255.,252./255.,171./255.,1.)
        self.couleur_zenith = hg.Color(70. / 255. / 2, 150. / 255. / 2, 255. / 255. / 2, 1.)

        self.couleur_ambiante = hg.Color(78. / 255., 119. / 255., 107. / 255., 1.)
        # self.couleur_ambiante=hg.Color(1,0,0,1)

        renderer = plus.GetRenderer()
        # -------------- Init le shader de rendu de terrain:
        self.shader_terrain = renderer.LoadShader("assets/shaders/terrain_marching_montagnes.isl")
        self.texture_terrain1 = renderer.LoadTexture("assets/textures/terrain_1.png")
        self.texture_terrain2 = renderer.LoadTexture("assets/textures/terrain_256.png")
        self.texture_terrain3 = renderer.LoadTexture("assets/textures/terrain_2048.png")
        self.texture_cosmos = renderer.LoadTexture("assets/textures/cosmos_b.png")

        self.facteur_echelle_terrain_l1 = hg.Vector2(20000, 20000)
        self.facteur_echelle_terrain_l2 = hg.Vector2(1000, 1000)
        self.facteur_echelle_terrain_l3 = hg.Vector2(100, 100)

        self.amplitude_l1 = 1000
        self.amplitude_l2 = 90
        self.amplitude_l3 = 1.5
        self.terrain_intensite_ambiante = 0.2

        self.offset_terrain = hg.Vector3(0, -50, 0)

        self.facteur_precision_distance = 1.01
        self.couleur_neige = hg.Color(0.91 * 0.75, 0.91 * 0.75, 1 * 0.75)
        self.couleur_cristaux = hg.Color(133 / 255, 225 / 255, 181 / 255, 1)
        self.couleur_eau = hg.Color(117. / 255., 219. / 255., 211. / 255.)
        self.altitude_eau = 0
        self.reflexion_eau = 0.5
        self.intensite_cristaux = 3


    def load_json_script(self,file_name="assets/scripts/terrain_parameters.json"):
        json_script = hg.GetFilesystem().FileToString(file_name)
        if json_script != "":
            script_parameters = json.loads(json_script)
            self.facteur_echelle_terrain_l1 = hg.Vector2(script_parameters["map1_scale_x"], script_parameters["map1_scale_y"])
            self.facteur_echelle_terrain_l2 = hg.Vector2(script_parameters["map2_scale_x"], script_parameters["map2_scale_y"])
            self.facteur_echelle_terrain_l3 = hg.Vector2(script_parameters["map3_scale_x"], script_parameters["map3_scale_y"])
            self.amplitude_l1 = script_parameters["map1_amplitude"]
            self.amplitude_l2 = script_parameters["map2_amplitude"]
            self.amplitude_l3 = script_parameters["map3_amplitude"]
            self.facteur_precision_distance = script_parameters["distance_factor"]
            self.altitude_eau = script_parameters["water_altitude"]
            self.reflexion_eau = script_parameters["water_reflexion"]
            self.offset_terrain.x = script_parameters["offset_x"]
            self.offset_terrain.y = script_parameters["offset_y"]
            self.offset_terrain.z = script_parameters["offset_z"]


    def save_json_script(self,output_filename = "assets/scripts/terrain_parameters.json"):
        script_parameters = {"map1_scale_x": self.facteur_echelle_terrain_l1.x,
                             "map1_scale_y": self.facteur_echelle_terrain_l1.y,
                             "map2_scale_x": self.facteur_echelle_terrain_l2.x,
                             "map2_scale_y": self.facteur_echelle_terrain_l2.y,
                             "map3_scale_x": self.facteur_echelle_terrain_l3.x,
                             "map3_scale_y": self.facteur_echelle_terrain_l3.y, "map1_amplitude": self.amplitude_l1,
                             "map2_amplitude": self.amplitude_l2, "map3_amplitude": self.amplitude_l3,
                             "distance_factor": self.facteur_precision_distance, "water_altitude": self.altitude_eau,
                             "water_reflexion": self.reflexion_eau,"offset_x": self.offset_terrain.x, "offset_y": self.offset_terrain.y,
                             "offset_z": self.offset_terrain.z}
        json_script = json.dumps(script_parameters, indent=4)
        return hg.GetFilesystem().StringToFile(output_filename, json_script)


    def update_shader(self,plus , scene, resolution):
        camera = scene.GetNode("Camera")
        renderer=plus.GetRenderer()
        renderer.EnableDepthTest(True)
        renderer.EnableDepthWrite(True)
        renderer.EnableBlending(False)

        #renderer.SetViewport(hg.fRect(0, 0, resolution.x, resolution.y))  # fit viewport to window dimensions
        #renderer.Clear(hg.Color.Black, 1, hg.GpuRenderer.ClearDepth)

        renderer.SetShader(self.shader_terrain)
        renderer.SetShaderTexture("texture_terrain", self.texture_terrain1)
        renderer.SetShaderTexture("texture_terrain2", self.texture_terrain2)
        renderer.SetShaderTexture("texture_terrain3", self.texture_terrain3)
        renderer.SetShaderTexture("texture_ciel", self.texture_cosmos)
        renderer.SetShaderFloat("ratio_ecran",resolution.x/resolution.y)
        renderer.SetShaderFloat("distanceFocale",camera.GetCamera().GetZoomFactor())
        cam=camera.GetTransform()
        camPos=cam.GetPosition()
        camPos=camPos-self.offset_terrain
        camPos.x+=self.facteur_echelle_terrain_l1.x/2
        camPos.z+=self.facteur_echelle_terrain_l1.y/2
        renderer.SetShaderFloat3("obs_pos",camPos.x-self.offset_terrain.x,camPos.y-self.offset_terrain.y,camPos.z-self.offset_terrain.z)
        renderer.SetShaderMatrix3("obs_mat_normale",cam.GetWorld().GetRotationMatrix())
        renderer.SetShaderFloat2("facteur_echelle_terrain1",1./self.facteur_echelle_terrain_l1.x,1./self.facteur_echelle_terrain_l1.y)
        renderer.SetShaderFloat2("facteur_echelle_terrain2",1./self.facteur_echelle_terrain_l2.x,1./self.facteur_echelle_terrain_l2.y)
        renderer.SetShaderFloat2("facteur_echelle_terrain3",1./self.facteur_echelle_terrain_l3.x,1./self.facteur_echelle_terrain_l3.y)
        renderer.SetShaderFloat("amplitude_terrain1",self.amplitude_l1)
        renderer.SetShaderFloat("amplitude_terrain2",self.amplitude_l2)
        renderer.SetShaderFloat("amplitude_terrain3",self.amplitude_l3)
        renderer.SetShaderFloat("facteur_precision_distance",self.facteur_precision_distance)
        renderer.SetShaderFloat("altitude_eau",self.altitude_eau)
        renderer.SetShaderFloat("reflexion_eau",self.reflexion_eau)
        renderer.SetShaderFloat("intensite_ambiante",self.terrain_intensite_ambiante)
        renderer.SetShaderFloat3("couleur_zenith",self.couleur_zenith.r,self.couleur_zenith.g,self.couleur_zenith.b)
        renderer.SetShaderFloat3("couleur_horizon",self.couleur_horizon.r,self.couleur_horizon.g,self.couleur_horizon.b)
        renderer.SetShaderFloat3("couleur_neige",self.couleur_neige.r,self.couleur_neige.g,self.couleur_neige.b)
        renderer.SetShaderFloat3("couleur_eau",self.couleur_eau.r,self.couleur_eau.g,self.couleur_eau.b)
        renderer.SetShaderFloat3("couleur_cristaux",self.couleur_cristaux.r*self.intensite_cristaux,\
                                   self.couleur_cristaux.g*self.intensite_cristaux,self.couleur_cristaux.b*self.intensite_cristaux)

        l_dir=self.lumiere_soleil.GetTransform().GetWorld().GetRotationMatrix().GetZ()

        renderer.SetShaderFloat3("l1_direction",l_dir.x,l_dir.y,l_dir.z)
        l_couleur=self.lumiere_soleil.GetLight().GetDiffuseColor()
        renderer.SetShaderFloat3("l1_couleur",l_couleur.r,l_couleur.g,l_couleur.b)

        l_dir=self.lumiere_ciel.GetTransform().GetWorld().GetRotationMatrix().GetZ()
        renderer.SetShaderFloat3("l2_direction",l_dir.x,l_dir.y,l_dir.z)
        l_couleur=self.lumiere_ciel.GetLight().GetDiffuseColor()*self.lumiere_ciel.GetLight().GetDiffuseIntensity()
        renderer.SetShaderFloat3("l2_couleur",l_couleur.r,l_couleur.g,l_couleur.b)

        renderer.SetShaderFloat2("zFrustum",camera.GetCamera().GetZNear(),camera.GetCamera().GetZFar())


# =============================================================================================

#       Fonctions

# =============================================================================================

def init_scene(plus):
    scene = plus.NewScene()
    camera = plus.AddCamera(scene,hg.Matrix4.TranslationMatrix(hg.Vector3(0, 0, -10)))
    camera.SetName("Camera")
    camera.GetCamera().SetZNear(1.)
    camera.GetCamera().SetZFar(10000)

    init_lights(plus, scene)
    fps = hg.FPSController(0,500,-10)

    while not scene.IsReady():                      # Wait until scene is ready
        plus.UpdateScene(scene, plus.UpdateClock())

    plus.UpdateScene(scene, plus.UpdateClock())

    return scene, fps


def init_lights(plus, scene):
    # Main light:
    ligth_sun = plus.AddLight(scene, hg.Matrix4.RotationMatrix(hg.Vector3(radians(22),radians(-45), 0)),
                            hg.LightModelLinear)
    ligth_sun.SetName("Sun")
    ligth_sun.GetLight().SetDiffuseColor(hg.Color(255. / 255., 255. / 255., 255. / 255., 1.))

    ligth_sun.GetLight().SetShadow(hg.LightShadowMap)  # Active les ombres portées
    ligth_sun.GetLight().SetShadowRange(100)

    ligth_sun.GetLight().SetDiffuseIntensity(1.)
    ligth_sun.GetLight().SetSpecularIntensity(1.)

    # Sky ligth:
    ligth_sky = plus.AddLight(scene, hg.Matrix4.RotationMatrix(hg.Vector3(radians(54), radians(135), 0)),
                            hg.LightModelLinear)
    ligth_sky.SetName("SkyLigth")
    ligth_sky.GetLight().SetDiffuseColor(hg.Color(103. / 255., 157. / 255., 141. / 255., 1.))
    ligth_sky.GetLight().SetDiffuseIntensity(0.9)


def init_terrain(plus,scene):
    terrain = TerrainMarching(plus,scene)
    terrain.load_json_script()
    return terrain


def gui_interface(terrain : TerrainMarching, scene, fps):

    camera = scene.GetNode("Camera")

    if hg.ImGuiBegin("Settings"):
        #f = hg.ImGuiInputVector2("Map 1 scale",terrain.facteur_echelle_terrain_l1,1)

        if hg.ImGuiButton("Load parameters"):
            terrain.load_json_script()
        hg.ImGuiSameLine()
        if hg.ImGuiButton("Save parameters"):
            terrain.save_json_script()
        if hg.ImGuiButton("Load camera"):
            load_fps_matrix(fps)
        hg.ImGuiSameLine()
        if hg.ImGuiButton("Save camera"):
            save_json_matrix(camera.GetTransform().GetPosition(),camera.GetTransform().GetRotation())

        f = hg.ImGuiColorEdit("Water color", terrain.couleur_eau, False)

        hg.ImGuiText("A/Q facteur_echelle_terrain_l1.x: " + str(terrain.facteur_echelle_terrain_l1.x))
        hg.ImGuiText("Z/S facteur_echelle_terrain_l1.y: " + str(terrain.facteur_echelle_terrain_l1.y))
        hg.ImGuiText("E/D facteur_echelle_terrain_l2.x: " + str(terrain.facteur_echelle_terrain_l2.x))
        hg.ImGuiText("R/F facteur_echelle_terrain_l2.y: " + str(terrain.facteur_echelle_terrain_l2.y))
        hg.ImGuiText("T/G facteur_echelle_terrain_l3.x: " + str(terrain.facteur_echelle_terrain_l3.x))
        hg.ImGuiText("Y/H facteur_echelle_terrain_l3.y: " + str(terrain.facteur_echelle_terrain_l3.y))
        hg.ImGuiText("U/J amplitude_l1: " + str(terrain.amplitude_l1))
        hg.ImGuiText("I/K amplitude_l2: " + str(terrain.amplitude_l2))
        hg.ImGuiText("O/L amplitude_l3: " + str(terrain.amplitude_l3))
        hg.ImGuiText("P/M facteur_precision_distance: " + str(terrain.facteur_precision_distance))
        hg.ImGuiText("1/2 altitude_eau: " + str(terrain.altitude_eau))
        hg.ImGuiText("3/4 reflexion_eau: " + str(terrain.reflexion_eau))
        hg.ImGuiText("5/6 offset terrain X: " + str(terrain.offset_terrain.x))
        hg.ImGuiText("7/8 offset terrain Y: " + str(terrain.offset_terrain.y))
        hg.ImGuiText("9/0 offset terrain Z: " + str(terrain.offset_terrain.z))
        hg.ImGuiText("CTRL+S sauve paramètres")
        hg.ImGuiText("CTRL+L charge paramètres")

    hg.ImGuiEnd()

def load_fps_matrix(fps):
    pos, rot = load_json_matrix()
    if pos is not None and rot is not None:
        fps.Reset(pos, rot)

def load_json_matrix(file_name="assets/scripts/camera_positions.json"):
    json_script = hg.GetFilesystem().FileToString(file_name)
    if json_script != "":
        pos = hg.Vector3()
        rot = hg.Vector3()
        script_parameters = json.loads(json_script)
        pos.x=script_parameters["x"]
        pos.y=script_parameters["y"]
        pos.z=script_parameters["z"]
        rot.x=script_parameters["rot_x"]
        rot.y=script_parameters["rot_y"]
        rot.z=script_parameters["rot_z"]
        return pos,rot
    return None,None

def save_json_matrix(pos : hg.Vector3, rot:hg.Vector3,output_filename = "assets/scripts/camera_positions.json"):
    script_parameters = {"x": pos.x,
                         "y": pos.y,
                         "z": pos.z,
                         "rot_x": rot.x,
                         "rot_y": rot.y,
                         "rot_z": rot.z}
    json_script = json.dumps(script_parameters, indent=4)
    return hg.GetFilesystem().StringToFile(output_filename, json_script)

def edition_clavier(terrain):
    if not plus.KeyDown(hg.KeyLCtrl):

        if plus.KeyDown(hg.KeyLAlt):
            f = 100
        else:
            f = 1

        if plus.KeyDown(hg.KeyA):
            terrain.facteur_echelle_terrain_l1.x += 100
        elif plus.KeyDown(hg.KeyQ):
            terrain.facteur_echelle_terrain_l1.x -= 100
            if terrain.facteur_echelle_terrain_l1.x < 100:
                terrain.facteur_echelle_terrain_l1.x = 100

        if plus.KeyDown(hg.KeyZ):
            terrain.facteur_echelle_terrain_l1.y += 100
        elif plus.KeyDown(hg.KeyS):
            terrain.facteur_echelle_terrain_l1.y -= 100
            if terrain.facteur_echelle_terrain_l1.y < 100:
                terrain.facteur_echelle_terrain_l1.y = 100

        if plus.KeyDown(hg.KeyE):
            terrain.facteur_echelle_terrain_l2.x += 10
        elif plus.KeyDown(hg.KeyD):
            terrain.facteur_echelle_terrain_l2.x -= 10
            if terrain.facteur_echelle_terrain_l2.x < 10:
                terrain.facteur_echelle_terrain_l2.x = 10

        if plus.KeyDown(hg.KeyR):
            terrain.facteur_echelle_terrain_l2.y += 10
        elif plus.KeyDown(hg.KeyF):
            terrain.facteur_echelle_terrain_l2.y -= 10
            if terrain.facteur_echelle_terrain_l2.y < 10:
                terrain.facteur_echelle_terrain_l2.y = 10

        if plus.KeyDown(hg.KeyT):
            terrain.facteur_echelle_terrain_l3.x += 0.1
        elif plus.KeyDown(hg.KeyG):
            terrain.facteur_echelle_terrain_l3.x -= 0.1
            if terrain.facteur_echelle_terrain_l3.x < 0.1:
                terrain.facteur_echelle_terrain_l3.x = 0.1

        if plus.KeyDown(hg.KeyY):
            terrain.facteur_echelle_terrain_l3.y += 0.1
        elif plus.KeyDown(hg.KeyH):
            terrain.facteur_echelle_terrain_l3.y -= 0.1
            if terrain.facteur_echelle_terrain_l3.y < 0.1:
                terrain.facteur_echelle_terrain_l3.y = 0.1

        elif plus.KeyDown(hg.KeyU):
            terrain.amplitude_l1 += 100
        elif plus.KeyDown(hg.KeyJ):
            terrain.amplitude_l1 -= 100
            # if terrain.amplitude_l1<100:
            # terrain.amplitude_l1=100

        elif plus.KeyDown(hg.KeyI):
            terrain.amplitude_l2 += 10
        elif plus.KeyDown(hg.KeyK):
            terrain.amplitude_l2 -= 10
            # if terrain.amplitude_l2<10:
            # terrain.amplitude_l2=10

        elif plus.KeyDown(hg.KeyO):
            terrain.amplitude_l3 += 0.05
        elif plus.KeyDown(hg.KeyL):
            terrain.amplitude_l3 -= 0.05
            # if terrain.amplitude_l3<0.05:
            # terrain.amplitude_l3=0.05


        elif plus.KeyDown(hg.KeyP):
            terrain.facteur_precision_distance += 0.001
        elif plus.KeyDown(hg.KeyM):
            terrain.facteur_precision_distance -= 0.001
            if terrain.facteur_precision_distance < 1.001:
                terrain.facteur_precision_distance = 1.001

        elif plus.KeyDown(hg.KeyNumpad2):
            terrain.altitude_eau += 1
        elif plus.KeyDown(hg.KeyNumpad1):
            terrain.altitude_eau -= 1

        elif plus.KeyDown(hg.KeyNumpad4):
            terrain.reflexion_eau += 0.01
        elif plus.KeyDown(hg.KeyNumpad3):
            terrain.reflexion_eau -= 0.01

        elif plus.KeyDown(hg.KeyNumpad6):
            terrain.offset_terrain.x += 0.1 * f
        elif plus.KeyDown(hg.KeyNumpad5):
            terrain.offset_terrain.x -= 0.1 * f

        elif plus.KeyDown(hg.KeyNumpad8):
            terrain.offset_terrain.y += 0.01 * f
        elif plus.KeyDown(hg.KeyNumpad7):
            terrain.offset_terrain.y -= 0.01 * f

        elif plus.KeyDown(hg.KeyNumpad0):
            terrain.offset_terrain.z += 0.1 * f
        elif plus.KeyDown(hg.KeyNumpad9):
            terrain.offset_terrain.z -= 0.1 * f

    elif plus.KeyDown(hg.KeyLCtrl):
        if plus.KeyPress(hg.KeyS):
            terrain.save_json_script()
        elif plus.KeyPress(hg.KeyL):
            terrain.load_parameters()

def update_view(plus, scene, fps, delta_t):
    camera = scene.GetNode("Camera")
    fps.UpdateAndApplyToNode(camera,delta_t)


# ==================================================================================================

#                                   Program start here

# ==================================================================================================

# Display settings
resolution = hg.Vector2(1600, 900)
antialiasing = 4
screenMode = hg.Windowed

# System setup
plus = hg.GetPlus()
hg.LoadPlugins()
plus.Mount("./")

# Run display
plus.RenderInit(int(resolution.x), int(resolution.y), antialiasing, screenMode)
plus.SetBlend2D(hg.BlendAlpha)

# Setup dashboard:
scene, fps = init_scene(plus)
render_to_texture = RenderToTexture(plus,resolution)
terrain = init_terrain(plus,scene)
load_fps_matrix(fps)

# -----------------------------------------------
#                   Main loop
# -----------------------------------------------

while not plus.KeyDown(hg.KeyEscape):
    delta_t = plus.UpdateClock()

    plus.GetRenderer().Clear(hg.Color.Black)  # red

    gui_interface(terrain, scene, fps)

    plus.UpdateScene(scene, delta_t)


    edition_clavier(terrain)

    render_to_texture.begin_render(plus)
    terrain.update_shader(plus, scene, resolution)
    render_to_texture.end_render(plus)

    update_view(plus, scene, fps, delta_t)

    plus.Flip()
    plus.EndFrame()

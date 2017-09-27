# -*-coding:Utf-8 -*

# ===========================================================

#              - Harfang - www.harfang3d.com

#                       - Python -

#               Basic post-rendering pipeline

# ===========================================================

import gs


# ===========================================================
#                           Functions
# ===========================================================

def display_render_texture():
    gs.DrawBuffers(renderer, 6, pr_indices, pr_vertex, pr_vertex_layout) #Fill the screen with 2 triangles


def display_post_render():

    # --- Main screen initializations:
    renderer.SetRenderTarget(None)
    renderer.SetViewport(gs.fRect(0, 0, window_size.x, window_size.y))  # fit viewport to window dimensions
    renderer.EnableBlending(False)
    renderer.EnableDepthTest(False)
    renderer.EnableDepthWrite(False)
    #renderer.Clear(gs.Color.Black) #No need to clear the screen, as it will be filled with the output texture.

    # --- Update post-rendering shader:
    renderer.SetShader(pr_shader)
    renderer.SetShaderTexture("u_tex", pr_texture_output)
    renderer.SetShaderFloat("contrast", pr_contrast)
    renderer.SetShaderFloat("contrast_threshold", pr_contrast_threshold)
    renderer.SetShaderFloat("hue", pr_hue)
    renderer.SetShaderFloat("saturation", pr_saturation)
    renderer.SetShaderFloat("value", pr_value)
    renderer.SetShaderFloat("fading_level", fading_level)
    renderer.SetShaderFloat4("fading_color",fading_color.r,fading_color.g,fading_color.b,fading_color.a)
    display_render_texture()


# ===========================================================
#                     Program starts ...
# ===========================================================

# --- Render parameters:

bitsDepth = 32
antialiasing_level = 4  # 1 to 8
window_mode = gs.Window.Windowed  # gs.Window.FullScreen

# --- Post-render parameters:

pr_contrast = 0
pr_contrast_threshold = 0.5
pr_hue = 1
pr_saturation = 1
pr_value = 1
fading_level = 0 #0(rendered pixels) to 1(fading color)
fading_color = gs.Color.Black

# --- File system:

gs.GetFilesystem().Mount(gs.StdFileDriver())  # Project root

# --- Initialize 3d renderer and output screen:

renderer = gs.EglRenderer()
renderer.Open(1280, 768, bitsDepth, window_mode)
renderer.Set2DMatrices()
renderer.EnableBlending(True)
renderer.EnableDepthTest(False)
window_size = renderer.GetDefaultOutputWindow().GetSize()

# --- Initialize render system:

system = gs.RenderSystem()
system.SetAA(antialiasing_level)
system.Initialize(renderer)

# --- Initialize 2d displays:

renderer2d = gs.SimpleGraphicEngine()
renderer2d.SetDepthWrite(False)
renderer2d.SetDepthTest(False)
renderer2d.SetBlendMode(gs.BlendAlpha)

# --- Get devices:

keyboard_device = gs.GetInputSystem().GetDevice("keyboard")

# --------------------------------------------
#               Init shaders
# --------------------------------------------

pr_shader = renderer.LoadShader("shaders/basic_filters.isl")
if pr_shader is None:
    exit("Error - Can't load shaders")

# --------------------------------------------
#       Create primitive vertex buffer
#       Used to display the output texture
# --------------------------------------------

# --- Vertices indices
data = gs.BinaryBlob()
data.WriteShorts([0, 1, 2, 0, 2, 3])
pr_indices = renderer.NewBuffer()
renderer.CreateBuffer(pr_indices, data, gs.GpuBuffer.Index)

# --- Vertices format:
pr_vertex_layout = gs.VertexLayout()
pr_vertex_layout.AddAttribute(gs.VertexAttribute.Position, 3, gs.VertexFloat)
pr_vertex_layout.AddAttribute(gs.VertexAttribute.UV0, 2, gs.VertexUByte,
                              True)  # UVs are sent as normalized 8 bit unsigned integer (range [0;255])

# --- Vertices coordinates:
data = gs.BinaryBlob()
x, y = 1, 1
data.WriteFloats([-x, -y, 0])       #Vertex coordinates
data.WriteUnsignedBytes([0, 0])     #Vertex U,V

data.WriteFloats([-x, y, 0])
data.WriteUnsignedBytes([0, 255])

data.WriteFloats([x, y, 0])
data.WriteUnsignedBytes([255, 255])

data.WriteFloats([x, -y, 0])
data.WriteUnsignedBytes([255, 0])

# --- Creates vertices buffer:
pr_vertex = renderer.NewBuffer()
renderer.CreateBuffer(pr_vertex, data, gs.GpuBuffer.Vertex)

# --------------------------------------------
#            Create render target
# --------------------------------------------

# --- Color texture:
pr_texture_output = renderer.NewTexture()
renderer.CreateTexture(pr_texture_output, window_size.x, window_size.y, gs.GpuTexture.RGBA8, gs.GpuTexture.NoAA,
                       gs.GpuTexture.UsageDefault, False)

# --- Depth texture:
pr_texture_output_depth = renderer.NewTexture()
renderer.CreateTexture(pr_texture_output_depth, window_size.x, window_size.y, gs.GpuTexture.Depth, gs.GpuTexture.NoAA,
                       gs.GpuTexture.UsageDefault, False)

# --- Render target (Color & Depth textures combination):
pr_renderTarget = renderer.NewRenderTarget()
renderer.CreateRenderTarget(pr_renderTarget)
renderer.SetRenderTargetColorTexture(pr_renderTarget, pr_texture_output)
renderer.SetRenderTargetDepthTexture(pr_renderTarget, pr_texture_output_depth)

# --------------------------------------------
#                   Main loop
# --------------------------------------------

while renderer.GetDefaultOutputWindow():

    gs.GetInputSystem().Update()    # Update the devices

    if keyboard_device.WasPressed(gs.InputDevice.KeyEscape):
        break

    # --- Start rendering:

    renderer.SetRenderTarget(pr_renderTarget)  # Pixels rendering to output texture.

    renderer.SetViewport(gs.fRect(0, 0, window_size.x, window_size.y))  # fit viewport to texture dimensions
    renderer.EnableDepthTest(True)
    renderer.EnableDepthWrite(True)

    renderer.Clear(gs.Color(0, 0, 1, 0))    #Fill the render target with blue

    # --- Custom rendering (2d/3d)

    # ...

    # --- Post rendering

    display_post_render()

    # --- End of frame:

    renderer.DrawFrame()
    renderer.EnableDepthWrite(False)
    renderer.EnableDepthTest(False)
    renderer.Set2DMatrices()
    renderer.SetCullFunc(gs.GpuRenderer.CullFront)
    renderer2d.Flush(system)
    renderer.EnableDepthTest(True)
    renderer.EnableDepthWrite(True)
    renderer.ShowFrame()
    renderer.UpdateOutputWindow()

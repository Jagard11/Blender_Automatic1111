# Save this file as stable_diffusion_connect.py

bl_info = {
    "name": "Stable Diffusion Connect",
    "author": "AI Assistant",
    "version": (1, 42, 0),
    "blender": (3, 4, 0),
    "location": "View3D > Sidebar > SD Connect",
    "description": "Connects to A1111 API using Img2Img with robust UI and image previews.",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}

import bpy
import requests
import json
import base64
import os
import time
import threading

# --- Global lists and helper functions (No changes) ---
CONTROLNET_MODELS, CONTROLNET_MODULES, SD_MODELS, SD_SAMPLERS = [], [], [], []
LAST_FETCH_TIME = 0
def reset_status_text():
    try:
        if bpy.context.scene and hasattr(bpy.context.scene, 'sd_props'):
            props = bpy.context.scene.sd_props; props.status_text = "Ready"; props.status_icon = "INFO"
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas: area.tag_redraw()
    except Exception: pass
    return None
def get_api_address():
    prefs = bpy.context.preferences.addons[__name__].preferences
    return f"http://{prefs.api_address}" if not prefs.api_address.startswith("http") else prefs.api_address
def fetch_api_data():
    global CONTROLNET_MODELS, CONTROLNET_MODULES, SD_MODELS, SD_SAMPLERS, LAST_FETCH_TIME
    if time.time() - LAST_FETCH_TIME < 300 and all([CONTROLNET_MODELS, CONTROLNET_MODULES, SD_MODELS, SD_SAMPLERS]): return True
    api_address = get_api_address()
    try:
        models_response = requests.get(f"{api_address}/controlnet/model_list", timeout=5); CONTROLNET_MODELS = models_response.json().get("model_list", []) if models_response.ok else []
        modules_response = requests.get(f"{api_address}/controlnet/module_list", timeout=5); CONTROLNET_MODULES = modules_response.json().get("module_list", []) if modules_response.ok else []
        sd_models_response = requests.get(f"{api_address}/sdapi/v1/sd-models", timeout=5); SD_MODELS = sd_models_response.json() if sd_models_response.ok else []
        samplers_response = requests.get(f"{api_address}/sdapi/v1/samplers", timeout=5); SD_SAMPLERS = samplers_response.json() if samplers_response.ok else []
        if all([CONTROLNET_MODELS, CONTROLNET_MODULES, SD_MODELS, SD_SAMPLERS]): LAST_FETCH_TIME = time.time(); return True
    except requests.exceptions.RequestException as e:
        print(f"SD Connect: API data fetch failed: {e}"); CONTROLNET_MODELS, CONTROLNET_MODULES, SD_MODELS, SD_SAMPLERS = [], [], [], []
    return False

# --- UI Properties, Preferences, Operators ---
class SDConnectProperties(bpy.types.PropertyGroup):
    # (Definitions omitted for brevity)
    camera:bpy.props.PointerProperty(name="Camera",type=bpy.types.Object,poll=lambda s,o:o.type=='CAMERA');positive_prompt:bpy.props.StringProperty(name="Positive Prompt",default="masterpiece, best quality");negative_prompt:bpy.props.StringProperty(name="Negative Prompt",default="lowres, bad anatomy, worst quality, low quality");sd_model:bpy.props.EnumProperty(name="Checkpoint",items=lambda s,c:[(m.get('title'),m.get('model_name'),'')for m in SD_MODELS]);sampler_name:bpy.props.EnumProperty(name="Sampling Method",items=lambda s,c:[(m.get('name'),m.get('name'),'')for m in SD_SAMPLERS]);steps:bpy.props.IntProperty(name="Sampling Steps",default=25,min=1,soft_max=150);cfg_scale:bpy.props.FloatProperty(name="CFG Scale",default=7,min=1,soft_max=30);denoising_strength:bpy.props.FloatProperty(name="Denoising Strength",default=0.75,min=0,max=1);seed:bpy.props.IntProperty(name="Seed",default=-1);cn_enable:bpy.props.BoolProperty(name="Enable",default=True);cn_pixel_perfect:bpy.props.BoolProperty(name="Pixel Perfect",default=True);cn_low_vram:bpy.props.BoolProperty(name="Low VRAM",default=False);controlnet_type:bpy.props.EnumProperty(name="Control Type",items=[('All','All','All'),('Canny','Canny',''),('Depth','Depth',''),('NormalMap','NormalMap',''),('OpenPose','OpenPose',''),('Scribble','Scribble',''),('SoftEdge','SoftEdge',''),('Segmentation','Segmentation',''),('MLSD','MLSD','')]);cn_preprocessor:bpy.props.EnumProperty(name="Preprocessor",items=lambda s,c:[('None','None','')]+[(m,m,'')for m in CONTROLNET_MODULES if c.scene.sd_props.controlnet_type.lower()in m.lower()or c.scene.sd_props.controlnet_type=='All']);cn_model:bpy.props.EnumProperty(name="Model",items=lambda s,c:[(m,m,'')for m in CONTROLNET_MODELS if c.scene.sd_props.controlnet_type.lower()in m.lower()or c.scene.sd_props.controlnet_type=='All']);cn_weight:bpy.props.FloatProperty(name="Control Weight",default=1,min=0,max=2);cn_start_step:bpy.props.FloatProperty(name="Starting Control Step",default=0,min=0,max=1);cn_end_step:bpy.props.FloatProperty(name="Ending Control Step",default=1,min=0,max=1);cn_control_mode:bpy.props.EnumProperty(name="Control Mode",items=[('0','Balanced','Balanced'),('1','My prompt is more important','Prompt is more important'),('2','ControlNet is more important','ControlNet is more important')],default='0');status_text:bpy.props.StringProperty(name="Status Text",default="Ready");status_icon:bpy.props.StringProperty(name="Status Icon",default="INFO");sent_image:bpy.props.PointerProperty(type=bpy.types.Image);returned_image:bpy.props.PointerProperty(type=bpy.types.Image)
class SDConnectPreferences(bpy.types.AddonPreferences):
    bl_idname=__name__;api_address:bpy.props.StringProperty(name="A1111 API Address",default="127.0.0.1:7860");network_timeout:bpy.props.IntProperty(name="Network Timeout (s)",description="Time in seconds before a generation request is considered failed",default=300,min=10,soft_max=1800)
    def draw(self,c):l=self.layout;l.prop(self,"api_address");l.prop(self,"network_timeout");l.operator("sd_connect.test_connection",icon='URL')
class SD_OT_TestConnection(bpy.types.Operator):
    bl_idname="sd_connect.test_connection";bl_label="Refresh API Data"
    def execute(self,c):reset_status_text();global LAST_FETCH_TIME;LAST_FETCH_TIME=0;[self.report({'INFO'},"Successfully connected and fetched API data.")if fetch_api_data()else self.report({'ERROR'},"Connection failed. Check console for details.")];c.area.tag_redraw();return{'FINISHED'}
class SD_OT_ViewImage(bpy.types.Operator):
    bl_idname="sd_connect.view_image";bl_label="View Image";bl_options={'REGISTER'}
    image_name:bpy.props.StringProperty()
    def execute(self,c):img=bpy.data.images.get(self.image_name);[self.report({'WARNING'},"Image not found.")if not img else(bpy.ops.screen.area_dupli('INVOKE_DEFAULT'),setattr(c.window.screen.areas[-1],'type','IMAGE_EDITOR'),setattr(c.window.screen.areas[-1].spaces.active,'image',img))];return{'FINISHED'}
class SD_OT_SaveImage(bpy.types.Operator):
    bl_idname="sd_connect.save_image";bl_label="Save Generated Image";bl_options={'REGISTER'}
    filepath:bpy.props.StringProperty(subtype="FILE_PATH")
    @classmethod
    def poll(cls,c):return c.scene.sd_props.returned_image is not None
    def invoke(self,c,e):p=c.scene.sd_props;self.filepath=f"{os.path.splitext(p.returned_image.name)[0]}.png";c.window_manager.fileselect_add(self);return{'RUNNING_MODAL'}
    def execute(self,c):p=c.scene.sd_props;img_to_save=p.returned_image;temp_img=bpy.data.images.new("TempSave",img_to_save.size[0],img_to_save.size[1]);temp_img.pixels.foreach_set(img_to_save.pixels);temp_img.filepath_raw=self.filepath;temp_img.file_format='PNG';temp_img.save();bpy.data.images.remove(temp_img);self.report({'INFO'},f"Image saved to {self.filepath}");return{'FINISHED'}

# --- Corrected and Definitive Copy Image Operator ---
class SD_OT_CopyToClipboard(bpy.types.Operator):
    """Copies the last generated image to the clipboard by using a temporary render result."""
    bl_idname = "sd_connect.copy_to_clipboard"
    bl_label = "Copy to Clipboard"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.sd_props.returned_image is not None

    def execute(self, context):
        props = context.scene.sd_props
        image_to_copy = props.returned_image

        render_result = bpy.data.images.get("Render Result")
        if not render_result:
            self.report({'ERROR'}, "Internal error: Could not find 'Render Result' image buffer.")
            return {'CANCELLED'}

        # Store original state
        original_size = (render_result.size[0], render_result.size[1])
        original_pixels = [p for p in render_result.pixels]

        try:
            # Hijack the render result
            render_result.scale(image_to_copy.size[0], image_to_copy.size[1])
            render_result.pixels.foreach_set(image_to_copy.pixels)
            
            # Use the only operator that copies to the system clipboard
            bpy.ops.render.copy_to_clipboard()
            
            self.report({'INFO'}, "Returned image copied to clipboard.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to copy image: {e}")
        finally:
            # Restore the original render result to prevent data loss
            render_result.scale(original_size[0], original_size[1])
            render_result.pixels.foreach_set(original_pixels)
            
        return {'FINISHED'}

class SD_OT_RenderAndGenerate(bpy.types.Operator):
    bl_idname="sd_connect.render_and_generate";bl_label="Generate Image";bl_options={'REGISTER','UNDO'}
    _timer=None;thread=None;thread_result=None;thread_error=None;_context=None;network_start_time=0
    def network_task(self,api,payload,timeout):
        try:self.thread_result=requests.post(url=f'{api}/sdapi/v1/img2img',json=payload,timeout=timeout)
        except Exception as e:self.thread_error=e
    def _start_async_tasks(self):
        c=self._context;p=c.scene.sd_props;prefs=c.preferences.addons[__name__].preferences;orig_fp=c.scene.render.filepath;temp_dir=bpy.app.tempdir;temp_fp=os.path.join(temp_dir,"sd_connect_sent.png");c.scene.render.filepath=temp_fp;bpy.ops.render.render(write_still=True);c.scene.render.filepath=orig_fp
        if p.sent_image:bpy.data.images.remove(p.sent_image)
        sent_img=bpy.data.images.load(temp_fp);sent_img.gl_load();p.sent_image=sent_img;p.sent_image.name=f"SD_Connect_Sent_{int(time.time())}.png";p.status_text="Processing...";p.status_icon="SORTTIME"
        for w in c.window_manager.windows:
            for a in w.screen.areas:a.tag_redraw()
        with open(temp_fp,"rb")as f:encoded=base64.b64encode(f.read()).decode('utf-8')
        control_mode_map={'0':'Balanced','1':'My prompt is more important','2':'ControlNet is more important'}
        cn_payload={"args":[{"image":encoded,"module":p.cn_preprocessor,"model":p.cn_model,"weight":p.cn_weight,"guidance_start":p.cn_start_step,"guidance_end":p.cn_end_step,"control_mode":control_mode_map.get(p.cn_control_mode,'Balanced'),"pixel_perfect":p.cn_pixel_perfect,"low_vram":p.cn_low_vram}]}if p.cn_enable else{}
        payload={"init_images":[encoded],"prompt":p.positive_prompt,"negative_prompt":p.negative_prompt,"seed":p.seed,"steps":p.steps,"cfg_scale":p.cfg_scale,"sampler_name":p.sampler_name,"denoising_strength":p.denoising_strength,"width":c.scene.render.resolution_x,"height":c.scene.render.resolution_y,"alwayson_scripts":{"controlnet":cn_payload}if p.cn_enable else{}}
        self.network_start_time=time.time();self.thread=threading.Thread(target=self.network_task,args=(get_api_address(),payload,prefs.network_timeout));self.thread.start();self._timer=c.window_manager.event_timer_add(0.5,window=c.window);return None
    def execute(self,c):
        p=c.scene.sd_props
        if p.status_text not in["Ready","Complete!","Error"]:self.report({'WARNING'},"Already processing a request.");return{'CANCELLED'}
        if not p.camera:self.report({'ERROR'},"Please select a camera.");return{'CANCELLED'}
        self._context=c;p.status_text="Rendering...";p.status_icon="RENDER_ANIMATION";c.area.tag_redraw();p.camera.data.show_background_images=False;bpy.app.timers.register(self._start_async_tasks,first_interval=0.01);c.window_manager.modal_handler_add(self);return{'RUNNING_MODAL'}
    def modal(self,c,e):
        p=c.scene.sd_props;prefs=c.preferences.addons[__name__].preferences
        if e.type=='ESC':self.cancel(c);self.report({'INFO'},"Generation cancelled.");return{'CANCELLED'}
        if e.type=='TIMER':
            if self.network_start_time and(time.time()-self.network_start_time>prefs.network_timeout):self.report({'ERROR'},f"Operation timed out after {prefs.network_timeout} seconds.");self.cancel(c);return{'CANCELLED'}
            if self.thread and self.thread.is_alive():return{'PASS_THROUGH'}
            if self._timer:c.window_manager.event_timer_remove(self._timer);self._timer=None
            else:return{'PASS_THROUGH'}
            if self.thread_error or(self.thread_result and not self.thread_result.ok):
                err=self.thread_error or f"API request failed with status {self.thread_result.status_code if self.thread_result else 'N/A'}"
                self.report({'ERROR'},str(err));p.status_text="Error";p.status_icon="ERROR"
            else:
                r=self.thread_result.json()
                if'images'in r and r['images']:
                    img_data=base64.b64decode(r['images'][0])
                    old_image_to_remove=p.returned_image
                    gen_img_name=f"SD_Connect_Result_{int(time.time())}.png"
                    gen_fp=os.path.join(bpy.app.tempdir,gen_img_name);
                    with open(gen_fp,"wb")as f:f.write(img_data)
                    gen_img=bpy.data.images.load(gen_fp);gen_img.gl_load();gen_img.name=gen_img_name;
                    p.returned_image=gen_img
                    cam_data=p.camera.data;bg_container=None
                    for bg in cam_data.background_images:
                        if bg.image and bg.image==old_image_to_remove:bg_container=bg;break
                    if bg_container:bg_container.image=gen_img
                    else:
                        bg_container=cam_data.background_images.new()
                        bg_container.image=gen_img;bg_container.alpha=0.5;bg_container.scale=1.0;bg_container.display_depth='FRONT'
                    if old_image_to_remove and old_image_to_remove!=gen_img:bpy.data.images.remove(old_image_to_remove)
                    cam_data.show_background_images=True;p.status_text="Complete!";p.status_icon="CHECKMARK"
                else:self.report({'ERROR'},"API response did not contain an image.");p.status_text="Error";p.status_icon="ERROR"
            bpy.app.timers.register(reset_status_text,first_interval=5.0);c.area.tag_redraw();return{'FINISHED'}
        return{'PASS_THROUGH'}
    def cancel(self,c):
        if self._timer:c.window_manager.event_timer_remove(self._timer);self._timer=None
        reset_status_text()

# --- UI Panel (No changes needed) ---
class VIEW3D_PT_SDConnectPanel(bpy.types.Panel):
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='SD Connect';bl_label="Stable Diffusion Connect"
    def draw_header(self,c):self.layout.operator("sd_connect.test_connection",text="",icon='FILE_REFRESH')
    def draw(self,c):
        l=self.layout;p=c.scene.sd_props
        if not all([SD_MODELS,SD_SAMPLERS]):b=l.box();b.label(text="Click Refresh to connect to API.",icon='INFO');b.operator("sd_connect.test_connection",text="Refresh API Data");return
        b=l.box();b.label(text="Main Settings");b.prop_search(p,"camera",c.scene,"objects",text="Camera");b.prop(p,"sd_model");b.prop(p,"sampler_name");col=b.column(align=True);row=col.row(align=True);row.prop(p,"steps");row.prop(p,"cfg_scale");col.prop(p,"denoising_strength",slider=True);b.prop(p,"seed");l.separator();b=l.box();l.label(text="Positive Prompt");pos_box=b.box();pos_box.prop(p,"positive_prompt",text="");l.label(text="Negative Prompt");neg_box=b.box();neg_box.prop(p,"negative_prompt",text="");cn_box=l.box();cn_box.prop(p,"cn_enable",text="ControlNet Unit 0")
        if p.cn_enable: cn_box.prop(p,"controlnet_type");col=cn_box.column(align=True);col.prop(p,"cn_preprocessor");col.prop(p,"cn_model");cn_box.separator();row=cn_box.row();row.prop(p,"cn_low_vram");row.prop(p,"cn_pixel_perfect");cn_box.prop(p,"cn_weight",slider=True);cn_box.prop(p,"cn_start_step",slider=True);cn_box.prop(p,"cn_end_step",slider=True);cn_box.prop(p,"cn_control_mode",expand=True)
        if p.camera:
            l.separator();cam_box=l.box();cam_box.label(text=f"Controls for: {p.camera.name}");col=cam_box.column(align=True);col.prop(p.camera.data,"lens",text="Lens (FoV)")
            bg_container=None
            for bg in p.camera.data.background_images:
                if bg.image and bg.image==p.returned_image:bg_container=bg;break
            if bg_container:
                col.prop(p.camera.data,"show_background_images",text="Show Background",toggle=True)
                row=col.row();row.enabled=p.camera.data.show_background_images;row.prop(bg_container,"alpha",slider=True)
                row=col.row();row.enabled=p.camera.data.show_background_images;row.prop(bg_container,"scale",text="Display Size")
            else:col.label(text="Generate image for BG controls.",icon='INFO')
        l.separator();s_box=l.box();col=s_box.column();row=col.row(align=True);row.alignment='CENTER';row.label(text=p.status_text,icon=p.status_icon);row=col.row();row.scale_y=1.5;row.operator("sd_connect.render_and_generate")
        l.separator();history_box=l.box();history_box.label(text="Image History");col=history_box.column(align=True)
        row_sent=col.row();row_sent.enabled=p.sent_image is not None;op_sent=row_sent.operator("sd_connect.view_image",text="View Sent Image",icon='IMAGE_RGB');
        if p.sent_image:op_sent.image_name=p.sent_image.name
        row_returned=col.row();row_returned.enabled=p.returned_image is not None;op_returned=row_returned.operator("sd_connect.view_image",text="View Returned Image",icon='IMAGE_RGB_ALPHA');
        if p.returned_image:op_returned.image_name=p.returned_image.name
        col.separator()
        row_actions=col.row(align=True)
        row_actions.operator("sd_connect.copy_to_clipboard",icon='COPYDOWN')
        row_actions.operator("sd_connect.save_image",icon='FILE_TICK')

# --- Registration ---
def on_load_handler(dummy):reset_status_text()
classes=[SDConnectPreferences,SDConnectProperties,SD_OT_TestConnection,SD_OT_ViewImage,SD_OT_SaveImage,SD_OT_CopyToClipboard,SD_OT_RenderAndGenerate,VIEW3D_PT_SDConnectPanel]
def register():
    for cls in classes:bpy.utils.register_class(cls)
    bpy.types.Scene.sd_props=bpy.props.PointerProperty(type=SDConnectProperties)
    bpy.app.handlers.load_post.append(on_load_handler)
    reset_status_text()
def unregister():
    for handler in bpy.app.handlers.load_post:
        if handler.__name__=="on_load_handler":bpy.app.handlers.load_post.remove(handler)
    for cls in reversed(classes):bpy.utils.unregister_class(cls)
    del bpy.types.Scene.sd_props
if __name__=="__main__":register()
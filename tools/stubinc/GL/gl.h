/* Minimal stand-in for GL/gl.h, used only by the Linux build of
 * cl_dll/particleman/CFrustum.cpp. That file needs just these two
 * constants; values are the ones from SDL_opengl.h. */
#ifndef GL_GL_H_STUB
#define GL_GL_H_STUB
#define GL_MODELVIEW_MATRIX  0x0BA6
#define GL_PROJECTION_MATRIX 0x0BA7
#endif

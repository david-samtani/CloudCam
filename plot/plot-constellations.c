/*
 # This file is part of the Astrometry.net suite.
 # Licensed under a 3-clause BSD style license - see LICENSE
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <sys/types.h>
#include <string.h>
#include <ctype.h>
#include <assert.h>

#include <cairo.h>

#include "an-bool.h"
#include "sip_qfits.h"
#include "starutil.h"
#include "bl.h"
#include "bl-sort.h"
#include "xylist.h"
#include "rdlist.h"
#include "boilerplate.h"
#include "mathutil.h"
#include "cairoutils.h"
#include "openngc.h"
#include "constellations.h"
#include "constellation-boundaries.h"
#include "brightstars.h"
#include "hd.h"
#include "fitsioutils.h"
#include "sip-utils.h"
#include "errors.h"
#include "log.h"

const char* OPTIONS = "hi:o:w:W:H:s:NCBpb:cjxvLn:f:MDd:G:g:JF:V:O:U:X:Y:";
char* usercat_fn = NULL;
char* usercat2_fn = NULL;
const char *custom_fn  = NULL;

void print_help(char* progname) {
    BOILERPLATE_HELP_HEADER(stdout);
    printf("\nUsage: %s\n"
           "   -w <WCS input file>\n"
           "   ( -L: just list the items in the field\n"
           " OR  -o <image output file; \"-\" for stdout>  )\n"
           "   [-p]: write PPM output - default is PNG\n"
           "   (  [-i <PPM input file>]\n"
           "   OR [-W <width> -H <height>] )\n"
           "   [-s <scale>]: scale image coordinates by this value before plotting.\n"
           "   [-N]: plot NGC objects\n"
           "   [-F <fraction>]: minimum NGC size, relative to image size (default 0.02)\n"
           "   [-C]: plot constellations\n"
           "   [-B]: plot named bright stars\n"
           "   [-D]: plot HD objects\n"
           "   [-d]: path to HD catalog\n"
           "   [-b <number-of-bright-stars>]: just plot the <N> brightest stars\n"
           "   [-c]: only plot bright stars that have common names.\n"
           "   [-j]: if a bright star has a common name, only print that\n"
           "   [-x]: plot only white text"
           "   [-v]: be verbose\n"
           "   [-n <width>]: NGC circle width (default 2)\n"
           "   [-f <size>]: font size.\n"
           "   [-M]: show only NGC/IC and Messier numbers (no common names)\n"
           "   [-G <grid spacing in arcmin>]: plot RA,Dec grid\n"
           "   [-g <r:g:b>]: grid color (default 0.2:0.2:0.2)\n"
           "   [-J]: print JSON output to stderr\n"
           "   [-V]: vertical alignment of text labels, \"C\"enter/\"T\"op/\"B\"ottom: default C\n"
           "   [-O]: horizontal alignment of text labels, \"L\"eft/\"C\"enter/\"R\"ight, default L\n"
           // additional command to plot additional objects
           "   [-U <ephemeris catalog file>]: plot user-supplied ephemeris objects (planets/satellites)\n"
           "   [-Y <custom catalog file>]: plot user-supplied custom objects (Hawaiian stars)\n"
           "   [-X <custom lines file>]: plot custom constellation line segments (e.g. Hawaiian)\n"

           "\n", progname);
}


static int sort_by_mag(const void* v1, const void* v2) {
    const brightstar_t* s1 = v1;
    const brightstar_t* s2 = v2;
    if (s1->Vmag > s2->Vmag)
        return 1;
    if (s1->Vmag == s2->Vmag)
        return 0;
    return -1;
}

struct cairos_t {
    cairo_t* fg;
    cairo_t* bg;
    cairo_t* shapes;
    cairo_t* shapesmask;
    int imgW;
    int imgH;
};
typedef struct cairos_t cairos_t;

static void add_text(cairos_t* cairos,
                     const char* txt, double px, double py,
                     char halign, char valign) {
    cairo_text_extents_t textents;
    double l,r,t,b;
    double margin = 2.0;
    int dx, dy;

    float offset = 15.;

    cairo_text_extents(cairos->fg, txt, &textents);
    l = px + textents.x_bearing;
    r = l + textents.width + textents.x_bearing;
    t = py + textents.y_bearing;
    b = t + textents.height;
    l -= margin;
    t -= margin;
    r += margin + 1;
    b += margin + 1;

    switch (valign) {
    case 'T':
        py -= (0.5 * textents.y_bearing);
        break;
    case 'B':
        py += (0.5 * textents.y_bearing) - offset;
        break;
    case 'C':
        break;
    }

    //logverb("halign=%c, width=%f\n", halign, textents.width);
    switch (halign) {
    case 'L':
        break;
    case 'C':
        px -= (0.5 * textents.width);
        break;
    case 'R':
        px -= (1.0 * textents.width);
        break;
    }


    // move text away from the edges of the image.
    if (l < 0) {
        px += -l;
        l = 0;
    }
    if (t < 0) {
        py += -t;
        t = 0;
    }
    if (r > cairos->imgW) {
        px -= (r - cairos->imgW);
        r = cairos->imgW;
    }
    if (b > cairos->imgH) {
        py -= (b - cairos->imgH);
        b = cairos->imgH;
    }
        
    // draw black text behind the white text, on the foreground layer.
//    cairo_save(cairos->fg);
  //  cairo_set_source_rgba(cairos->fg, 0, 0, 0, 1);
    //for (dy=-1; dy<=1; dy++) {
      //  for (dx=-1; dx<=1; dx++) {
        //    cairo_move_to(cairos->fg, px+dx, py+dy);
          //  cairo_show_text(cairos->fg, txt);
            //cairo_stroke(cairos->fg);
      //  }
    //}
  //  cairo_restore(cairos->fg);

    // draw the white text.
    cairo_move_to(cairos->fg, px, py);
    cairo_show_text(cairos->fg, txt);
    cairo_stroke(cairos->fg);

    // blank out anything on the lower layers underneath the text.
    cairo_save(cairos->shapesmask);
    cairo_set_source_rgba(cairos->shapesmask, 0, 0, 0, 0);
    cairo_set_operator(cairos->shapesmask, CAIRO_OPERATOR_SOURCE);
    cairo_move_to(cairos->shapesmask, l, t);
    cairo_line_to(cairos->shapesmask, l, b);
    cairo_line_to(cairos->shapesmask, r, b);
    cairo_line_to(cairos->shapesmask, r, t);
    cairo_close_path(cairos->shapesmask);
    cairo_fill(cairos->shapesmask);
    cairo_stroke(cairos->shapesmask);
    cairo_restore(cairos->shapesmask);

}

static void color_for_radec(double ra, double dec, float* r, float* g, float* b) {
    int con = constellation_containing(ra, dec);
    srand(con);
    *r = ((rand() % 128) + 127) / 255.0;
    *g = ((rand() % 128) + 127) / 255.0;
    *b = ((rand() % 128) + 127) / 255.0;
}

/**
 * Draw Hawaiian (or any custom) constellation stick figures.
 * File format:
 *   # Constellation Name (optional English in parentheses)
 *   StarA  raA(deg)  decA(deg)   StarB  raB(deg)  decB(deg)
 *   ...
 * A blank line or a new '#' line starts a new constellation.
 */

/**
 * Draw Hawaiian (or any custom) constellation stick figures.
 * File format:
 *   # Constellation Name (optional English in parentheses)
 *   StarA  raA(deg)  decA(deg)   StarB  raB(deg)  decB(deg)
 *   ...
 * A blank line or a new '#' line starts a new constellation.
 */
static void
draw_custom_constellations(cairos_t* cairos,
                           const sip_t* sip,
                           int W, int H,
                           const char* fn)
{
    FILE* f = fopen(fn, "r");
    if (!f) {
        fprintf(stderr, "[custom] cannot open %s\n", fn);
        return;
    }

    /* ---- Simple Cohen–Sutherland clipper implemented via macros ---- */
    #define CS_LEFT   1
    #define CS_RIGHT  2
    #define CS_BOTTOM 4
    #define CS_TOP    8
    #define OUTCODE(_x,_y,_xmin,_ymin,_xmax,_ymax) \
        (((_x) < (_xmin) ? CS_LEFT : ((_x) > (_xmax) ? CS_RIGHT : 0)) | \
         ((_y) < (_ymin) ? CS_BOTTOM : ((_y) > (_ymax) ? CS_TOP   : 0)))

    /* Clips segment (x1,y1)-(x2,y2) to [0..VW]x[0..VH]; sets _accept=1 if any remains */
    #define CLIP_TO_VIEW(x1,y1,x2,y2,VW,VH,_accept) do {                 \
        double _xmin = 0.0, _ymin = 0.0, _xmax = (double)(VW), _ymax = (double)(VH); \
        int _c1 = OUTCODE((x1),(y1),_xmin,_ymin,_xmax,_ymax);             \
        int _c2 = OUTCODE((x2),(y2),_xmin,_ymin,_xmax,_ymax);             \
        _accept = 0;                                                      \
        while (1) {                                                       \
            if (!(_c1 | _c2)) { _accept = 1; break; }                     \
            if (_c1 & _c2) { _accept = 0; break; }                        \
            double _x=0, _y=0; int _c = _c1 ? _c1 : _c2;                  \
            if (_c & CS_TOP)    { _x = (x1) + ((x2)-(x1)) * ((_ymax-(y1))/((y2)-(y1))); _y = _ymax; } \
            else if (_c & CS_BOTTOM){ _x = (x1) + ((x2)-(x1)) * ((_ymin-(y1))/((y2)-(y1))); _y = _ymin; } \
            else if (_c & CS_RIGHT){ _y = (y1) + ((y2)-(y1)) * ((_xmax-(x1))/((x2)-(x1))); _x = _xmax; } \
            else /* CS_LEFT */  { _y = (y1) + ((y2)-(y1)) * ((_xmin-(x1))/((x2)-(x1))); _x = _xmin; } \
            if (_c == _c1) { (x1) = _x; (y1) = _y; _c1 = OUTCODE((x1),(y1),_xmin,_ymin,_xmax,_ymax); } \
            else           { (x2) = _x; (y2) = _y; _c2 = OUTCODE((x2),(y2),_xmin,_ymin,_xmax,_ymax); } \
        }                                                                 \
    } while (0)

    /* Tests if segment intersects rect [rx,ry]..[rx+rw,ry+rh] (via clipping). */
    #define SEG_INTERSECTS_RECT(x1,y1,x2,y2, rx,ry,rw,rh, _hit) do {     \
        double _sx1 = (x1)-(rx), _sy1 = (y1)-(ry), _sx2 = (x2)-(rx), _sy2 = (y2)-(ry); \
        int _acc;                                                         \
        CLIP_TO_VIEW(_sx1,_sy1,_sx2,_sy2,(rw),(rh),_acc);                 \
        _hit = _acc;                                                      \
    } while (0)

    /* ------------------- Per-drawing setup ------------------- */
    const double LINE_W = 1.69;  /* requested line width */
    cairo_set_line_width(cairos->shapes,      LINE_W);
    cairo_set_source_rgba(cairos->shapes,     1.0, 1.0, 1.0, 1.0);
    cairo_set_line_width(cairos->shapesmask,  LINE_W);
    cairo_set_source_rgba(cairos->shapesmask, 1.0, 1.0, 1.0, 1.0);

    /* Track previous label area to avoid overdraw by subsequent segments */
    double text_area_x = 0.0, text_area_y = 0.0, text_area_w = 0.0, text_area_h = 0.0;
    int has_active_text = 0;

    /* Current constellation state */
    char   cur_label[128] = "";
    double cmx = 0.0, cmy = 0.0, cmz = 0.0;  /* spherical centroid accumulators */
    int    cmcount = 0;
    int    vis_star_count = 0;               /* counts endpoints on-screen in this block */

    /* Flush helper: draw label using stable centroid only if >=1 star is visible, then reset.
       Also clamp label CENTER so the entire text remains on-screen. */
    #define FLUSH_LABEL()                                                     \
    do {                                                                      \
        if (cmcount > 0 && cur_label[0] && vis_star_count > 0) {              \
            /* normalize centroid and convert to RA/Dec */                    \
            double norm = sqrt(cmx*cmx + cmy*cmy + cmz*cmz);                  \
            if (norm > 0.0) { cmx/=norm; cmy/=norm; cmz/=norm; }              \
            double sra=0.0, sdec=0.0, px=0.0, py=0.0;                         \
            xyzarr2radecdeg((double[3]){cmx,cmy,cmz}, &sra, &sdec);           \
            /* project to pixels (even if anchor is outside, we’ll clamp inside) */ \
            if (sip_radec2pixelxy(sip, sra, sdec, &px, &py)) {                \
                /* measure text */                                            \
                cairo_text_extents_t ext;                                     \
                cairo_set_font_size(cairos->fg, 34.0);                        \
                cairo_text_extents(cairos->fg, cur_label, &ext);              \
                /* clamp CENTER so full text fits on-screen (pad accounts for margins) */ \
                const double pad = 6.0;                                       \
                double min_cx = ext.width * 0.5 + pad;                        \
                double max_cx = (double)W - ext.width * 0.5 - pad;            \
                double min_cy = ext.height * 0.5 + pad;                       \
                double max_cy = (double)H - ext.height * 0.5 - pad;           \
                if (px < min_cx) px = min_cx; else if (px > max_cx) px = max_cx; \
                if (py < min_cy) py = min_cy; else if (py > max_cy) py = max_cy; \
                /* record text area for masking against NEXT segments */      \
                text_area_x = px - (ext.width/2) - 5;                          \
                text_area_y = py - (ext.height/2) - 5;                         \
                text_area_w = ext.width + 10;                                  \
                text_area_h = ext.height + 10;                                 \
                has_active_text = 1;                                          \
                /* clear any lines beneath the label on the shapes layer */   \
                cairo_save(cairos->shapes);                                   \
                cairo_set_operator(cairos->shapes, CAIRO_OPERATOR_CLEAR);     \
                cairo_rectangle(cairos->shapes, text_area_x, text_area_y,     \
                                text_area_w, text_area_h);                    \
                cairo_fill(cairos->shapes);                                   \
                cairo_restore(cairos->shapes);                                \
                /* draw the label itself (white), centered */                 \
                cairo_set_source_rgba(cairos->fg, 1.0, 1.0, 1.0, 1.0);        \
                add_text(cairos, cur_label, px, py, 'C', 'C');                \
                cairo_set_font_size(cairos->fg, 25.0);                        \
            }                                                                 \
        }                                                                     \
        /* reset accumulators for the next block */                           \
        cur_label[0] = '\0';                                                  \
        cmx = cmy = cmz = 0.0;                                                \
        cmcount = 0;                                                          \
        vis_star_count = 0;                                                   \
    } while (0)

    /* --------------- Parse file and draw segments --------------- */
    char   buf[256];
    char   name1[64], name2[64];
    double ra1=0.0, dec1=0.0, ra2=0.0, dec2=0.0;

    while (fgets(buf, sizeof(buf), f)) {
        /* new constellation header */
        if (buf[0] == '#') {
            FLUSH_LABEL();
            /* copy label (after '#'), trim newline */
            strncpy(cur_label, buf + 1, sizeof(cur_label) - 1);
            cur_label[sizeof(cur_label)-1] = '\0';
            cur_label[strcspn(cur_label, "\r\n")] = '\0';
            continue;
        }

        /* skip blanks */
        if (isspace((unsigned char)buf[0]))
            continue;

        /* parse one segment */
        if (sscanf(buf, "%63s %lf %lf %63s %lf %lf",
                   name1, &ra1, &dec1,
                   name2, &ra2, &dec2) != 6)
            continue;

        /* accumulate endpoints for stable centroid (regardless of visibility) */
        {
            double xyz[3];
            radecdeg2xyzarr(ra1, dec1, xyz);
            cmx += xyz[0]; cmy += xyz[1]; cmz += xyz[2]; cmcount++;
            radecdeg2xyzarr(ra2, dec2, xyz);
            cmx += xyz[0]; cmy += xyz[1]; cmz += xyz[2]; cmcount++;
        }

        /* project endpoints to pixel space */
        double x1=0.0, y1=0.0, x2=0.0, y2=0.0;
        if (!sip_radec2pixelxy(sip, ra1, dec1, &x1, &y1)) continue;
        if (!sip_radec2pixelxy(sip, ra2, dec2, &x2, &y2)) continue;

        /* count visible stars (endpoints) on screen for label gating */
        if (x1 >= 0 && x1 < W && y1 >= 0 && y1 < H) vis_star_count++;
        if (x2 >= 0 && x2 < W && y2 >= 0 && y2 < H) vis_star_count++;

        /* clip to viewport; skip if fully outside */
        int accept = 0;
        double cx1 = x1, cy1 = y1, cx2 = x2, cy2 = y2;
        CLIP_TO_VIEW(cx1, cy1, cx2, cy2, (double)W, (double)H, accept);
        if (!accept) continue;

        /* safe trim at both ends so lines don't butt into star glyphs */
        const double R = 25.0;
        double vx = cx2 - cx1, vy = cy2 - cy1;
        double d  = hypot(vx, vy);
        if (d <= 0.0 || !isfinite(d)) continue;
        double trim = fmin(R, d * 0.45); /* at most ~45% per end */
        double ux = vx / d,  uy = vy / d;
        double sx = cx1 + ux * trim, sy = cy1 + uy * trim;
        double ex = cx2 - ux * trim, ey = cy2 - uy * trim;

        if (!isfinite(sx) || !isfinite(sy) || !isfinite(ex) || !isfinite(ey))
            continue;

        /* avoid drawing under the previous label's text rectangle */
        int overlaps_text = 0;
        if (has_active_text) {
            SEG_INTERSECTS_RECT(sx, sy, ex, ey, text_area_x, text_area_y, text_area_w, text_area_h, overlaps_text);
        }
        if (!overlaps_text) {
            cairo_move_to(cairos->shapes, sx, sy);
            cairo_line_to(cairos->shapes, ex, ey);
            cairo_stroke(cairos->shapes);

            cairo_move_to(cairos->shapesmask, sx, sy);
            cairo_line_to(cairos->shapesmask, ex, ey);
            cairo_stroke(cairos->shapesmask);
        }
    }

    /* flush last block */
    FLUSH_LABEL();

    fclose(f);

    /* cleanup macro namespace */
    #undef SEG_INTERSECTS_RECT
    #undef CLIP_TO_VIEW
    #undef OUTCODE
    #undef CS_TOP
    #undef CS_BOTTOM
    #undef CS_RIGHT
    #undef CS_LEFT
}


int main(int argc, char** args) {
    int c;
    char* wcsfn = NULL;
    char* outfn = NULL;
    char* infn = NULL;
    sip_t sip;
    double scale = 1.0;
    anbool pngformat = TRUE;

    char* hdpath = NULL;
    anbool HD = FALSE;

    cairos_t thecairos;
    cairos_t* cairos = &thecairos;

    cairo_surface_t* target = NULL;
    cairo_t* cairot = NULL;

    cairo_surface_t* surfbg = NULL;
    cairo_t* cairobg = NULL;

    cairo_surface_t* surfshapes = NULL;
    cairo_t* cairoshapes = NULL;

    cairo_surface_t* surfshapesmask = NULL;
    cairo_t* cairoshapesmask = NULL;

    cairo_surface_t* surffg = NULL;
    cairo_t* cairo = NULL;

    double lw = 1.69;
    // circle linewidth.
    double cw = 0.0;

    double ngc_fraction = 0.02;

    // NGC linewidth
    double nw = 2.0;

    // leave a gap short of connecting the points.
    double endgap = 17.5;
    // circle radius.
    double crad = endgap;

    double fontsize = 25.0;

    double label_offset = 15.0;

    int W = 0, H = 0;
    unsigned char* img = NULL;

    anbool NGC = FALSE, constell = FALSE;
    anbool bright = FALSE;
    anbool common_only = FALSE;
    anbool print_common_only = FALSE;
    int Nbright = 0;
    double ra, dec, px, py;
    int i, N;
    anbool justlist = FALSE;
    anbool only_messier = FALSE;

    anbool grid = FALSE;
    double gridspacing = 0.0;
    double gridcolor[3] = { 0.2, 0.2, 0.2 };

    int loglvl = LOG_MSG;

    char halign = 'L';
    char valign = 'C';
    sl* json = NULL;

    anbool whitetext = FALSE;
    
    anbool custom = FALSE;     /* new */

    while ((c = getopt(argc, args, OPTIONS)) != -1) {
        switch (c) {
        case 'V':
            valign = optarg[0];
            break;
        case 'O':
            halign = optarg[0];
            break;
        case 'F':
            ngc_fraction = atof(optarg);
            break;
        case 'h':
            print_help(args[0]);
            exit(0);
        case 'J':
            json = sl_new(4);
            break;
        case 'G':
            gridspacing = atof(optarg);
            break;
        case 'g':
            {
                char *tail = NULL;
                gridcolor[0] = strtod(optarg,&tail);
                if (*tail) { tail++; gridcolor[1] = strtod(tail,&tail); }
                if (*tail) { tail++; gridcolor[2] = strtod(tail,&tail); }
            }
            break;
        case 'D':
            HD = TRUE;
            break;
        case 'd':
            hdpath = optarg;
            break;
        case 'M':
            only_messier = TRUE;
            break;
        case 'n':
            nw = atof(optarg);
            break;
        case 'f':
            fontsize = atof(optarg);
            break;
        case 'L':
            justlist = TRUE;
            outfn = NULL;
            break;
        case 'x':
            whitetext = TRUE;
            break;
        case 'v':
            loglvl++;
            break;
            break;
        case 'j':
            print_common_only = TRUE;
            break;
        case 'c':
            common_only = TRUE;
            break;
        case 'b':
            Nbright = atoi(optarg);
            break;
        case 'B':
            bright = TRUE;
            break;
        case 'N':
            NGC = TRUE;
            break;
        case 'C':
            constell = TRUE;
            break;
        case 'p':
            pngformat = FALSE;
            break;
        case 's':
            scale = atof(optarg);
            break;
        case 'o':
            outfn = optarg;
            break;
        case 'i':
            infn = optarg;
            break;
        case 'w':
            wcsfn = optarg;
            break;
        case 'W':
            W = atoi(optarg);
            break;
        case 'H':
            H = atoi(optarg);
            break;
        // new case to plot planets
        case 'U':
            usercat_fn = optarg;
            custom = TRUE;
            break;
        // new case to plot custom objects
        case 'Y':
            usercat2_fn = optarg;
            custom = TRUE;
            break;
        case 'X':  /* custom-constellation lines */
            custom_fn = optarg;
            custom = TRUE;
            break;
        }
    }

    log_init(loglvl);
    log_to(stderr);
    fits_use_error_system();

    if (optind != argc) {
        print_help(args[0]);
        exit(-1);
    }

    if (!(outfn || justlist) || !wcsfn) {
        logerr("Need (-o or -L) and -w args.\n");
        print_help(args[0]);
        exit(-1);
    }

    // read WCS.
    logverb("Trying to parse SIP/TAN header from %s...\n", wcsfn);
    if (!file_exists(wcsfn)) {
        ERROR("No such file: \"%s\"", wcsfn);
        exit(-1);
    }
    if (sip_read_header_file(wcsfn, &sip)) {
        logverb("Got SIP header.\n");
    } else {
        ERROR("Failed to parse SIP/TAN header from %s", wcsfn);
        exit(-1);
    }

    if (!(NGC || constell || bright || HD || grid || custom)) {
        logerr("Neither constellations, bright stars, HD nor NGC/IC overlays selected!\n");
        print_help(args[0]);
        exit(-1);
    }

    if (gridspacing > 0.0)
        grid = TRUE;

    // adjust for scaling...
    lw /= scale;
    cw /= scale;
    nw /= scale;
    crad /= scale;
    endgap /= scale;
    fontsize /= scale;
    label_offset /= scale;

    if (!W || !H) {
        W = sip.wcstan.imagew;
        H = sip.wcstan.imageh;
    }
    if (!(infn || (W && H))) {
        logerr("Image width/height unspecified, and no input image given.\n");
        exit(-1);
    }


    if (infn) {
        cairoutils_fake_ppm_init();
        img = cairoutils_read_ppm(infn, &W, &H);
        if (!img) {
            ERROR("Failed to read input image %s", infn);
            exit(-1);
        }
        cairoutils_rgba_to_argb32(img, W, H);
    } else if (!justlist) {
        // Allocate a black image.
        img = calloc(4 * W * H, 1);
        if (!img) {
            SYSERROR("Failed to allocate a blank image on which to plot!");
            exit(-1);
        }
    }

    if (HD && !hdpath) {
        logerr("If you specify -D (plot Henry Draper objs), you also have to give -d (path to Henry Draper catalog)\n");
        exit(-1);
    }

    if (!justlist) {
        /*
         Cairo layers:

         -background: surfbg / cairobg
         --> gets drawn first, in black, masked by surfshapesmask

         -shapes: surfshapes / cairoshapes
         --> gets drawn second, masked by surfshapesmask

         -foreground/text: surffg / cairo
         --> gets drawn last.
         */
        surffg = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, W, H);
        cairo = cairo_create(surffg);
        cairo_set_line_join(cairo, CAIRO_LINE_JOIN_BEVEL);
        cairo_set_antialias(cairo, CAIRO_ANTIALIAS_GRAY);
        cairo_set_source_rgba(cairo, 1.0, 1.0, 1.0, 1.0);
        cairo_scale(cairo, scale, scale);
        //cairo_select_font_face(cairo, "helvetica", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
        cairo_select_font_face(cairo, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
        cairo_set_font_size(cairo, fontsize);

        surfshapes = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, W, H);
        cairoshapes = cairo_create(surfshapes);
        cairo_set_line_join(cairoshapes, CAIRO_LINE_JOIN_BEVEL);
        cairo_set_antialias(cairoshapes, CAIRO_ANTIALIAS_GRAY);
        cairo_set_source_rgba(cairoshapes, 1.0, 1.0, 1.0, 1.0);
        cairo_scale(cairoshapes, scale, scale);
        cairo_select_font_face(cairoshapes, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
        cairo_set_font_size(cairoshapes, fontsize);

        surfshapesmask = cairo_image_surface_create(CAIRO_FORMAT_A8, W, H);
        cairoshapesmask = cairo_create(surfshapesmask);
        cairo_set_line_join(cairoshapesmask, CAIRO_LINE_JOIN_BEVEL);
        cairo_set_antialias(cairoshapesmask, CAIRO_ANTIALIAS_GRAY);
        cairo_set_source_rgba(cairoshapesmask, 1.0, 1.0, 1.0, 1.0);
        cairo_scale(cairoshapesmask, scale, scale);
        cairo_select_font_face(cairoshapesmask, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
        cairo_set_font_size(cairoshapesmask, fontsize);
        cairo_paint(cairoshapesmask);
        cairo_stroke(cairoshapesmask);

        surfbg = cairo_image_surface_create(CAIRO_FORMAT_A8, W, H);
        cairobg = cairo_create(surfbg);
        cairo_set_line_join(cairobg, CAIRO_LINE_JOIN_BEVEL);
        cairo_set_antialias(cairobg, CAIRO_ANTIALIAS_GRAY);
        cairo_set_source_rgba(cairobg, 0, 0, 0, 1);
        cairo_scale(cairobg, scale, scale);
        cairo_select_font_face(cairobg, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
        cairo_set_font_size(cairobg, fontsize);

        cairos->bg = cairobg;
        cairos->fg = cairo;
        cairos->shapes = cairoshapes;
        cairos->shapesmask = cairoshapesmask;
        cairos->imgW = (float)W/scale;
        cairos->imgH = (float)H/scale;
        //    }

        if (grid) {
            double ramin, ramax, decmin, decmax;
            double ra, dec;
            double rastep = gridspacing / 60.0;
            double decstep = gridspacing / 60.0;
            // how many line segments
            int N = 10;
            double px, py;
            int i;

            cairo_set_source_rgba(cairo, gridcolor[0], gridcolor[1], gridcolor[2], 1.0);

            sip_get_radec_bounds(&sip, 100, &ramin, &ramax, &decmin, &decmax);
            logverb("Plotting grid lines from RA=%g to %g in steps of %g; Dec=%g to %g in steps of %g\n",
                    ramin, ramax, rastep, decmin, decmax, decstep);
            for (dec = decstep * floor(decmin / decstep); dec<=decmax; dec+=decstep) {
                logverb("  dec=%g\n", dec);
                for (i=0; i<=N; i++) {
                    ra = ramin + ((double)i / (double)N) * (ramax - ramin);
                    if (!sip_radec2pixelxy(&sip, ra, dec, &px, &py))
                        continue;
                    // first time, move_to; else line_to
                    ((ra == ramin) ? cairo_move_to : cairo_line_to)(cairo, px, py);
                }
                cairo_stroke(cairo);
            }
            for (ra = rastep * floor(ramin / rastep); ra <= ramax; ra += rastep) {
                //for (dec=decmin; dec<=decmax; dec += (decmax - decmin)/(double)N) {
                logverb("  ra=%g\n", ra);
                for (i=0; i<=N; i++) {
                    dec = decmin + ((double)i / (double)N) * (decmax - decmin);
                    if (!sip_radec2pixelxy(&sip, ra, dec, &px, &py))
                        continue;
                    // first time, move_to; else line_to
                    ((dec == decmin) ? cairo_move_to : cairo_line_to)(cairo, px, py);
                }
                cairo_stroke(cairo);
            }

            cairo_set_source_rgba(cairo, 1.0, 1.0, 1.0, 1.0);
        }
    }

    if (constell) {
        N = constellations_n();

        logverb("Checking %i constellations.\n", N);
        for (c=0; c<N; c++) {
            const char* shortname = NULL;
            const char* longname;
            il* lines;
            il* uniqstars;
            il* inboundstars;
            float r,g,b;
            int Ninbounds;
            int Nunique;
            cairo_text_extents_t textents;
            double cmass[3];

            uniqstars = constellations_get_unique_stars(c);
            inboundstars = il_new(16);

            // --- Stable label anchor from ALL constellation members (spherical mean) ---
            double label_ra = 0.0, label_dec = 0.0;
            {
                double cm3[3] = {0,0,0};
                for (i = 0; i < il_size(uniqstars); i++) {
                    int s = il_get(uniqstars, i);
                    double sra, sdec, xyz[3];
                    constellations_get_star_radec(s, &sra, &sdec);
                    radecdeg2xyzarr(sra, sdec, xyz);
                    cm3[0] += xyz[0];
                    cm3[1] += xyz[1];
                    cm3[2] += xyz[2];
                }
                cm3[0] /= il_size(uniqstars);
                cm3[1] /= il_size(uniqstars);
                cm3[2] /= il_size(uniqstars);
                xyzarr2radecdeg(cm3, &label_ra, &label_dec);
            }

            Nunique = il_size(uniqstars);
            debug("%s: %zu unique stars.\n", shortname, il_size(uniqstars));

            // Count the number of unique stars belonging to this contellation
            // that are within the image bounds
            Ninbounds = 0;
            for (i=0; i<il_size(uniqstars); i++) {
                int star;
                star = il_get(uniqstars, i);
                constellations_get_star_radec(star, &ra, &dec);
                debug("star %i: ra,dec (%g,%g)\n", il_get(uniqstars, i), ra, dec);
                if (!sip_radec2pixelxy(&sip, ra, dec, &px, &py))
                    continue;
                if (px < 0 || py < 0 || px*scale > W || py*scale > H)
                    continue;
                Ninbounds++;
                il_append(inboundstars, star);
            }
            il_free(uniqstars);
            debug("%i are in-bounds.\n", Ninbounds);
            // Only draw this constellation if at least 2 of its stars
            // are within the image bounds.
            if (Ninbounds < 2) {
                il_free(inboundstars);
                continue;
            }

            // Set the color based on the location of the first in-bounds star.
            // This is a hack -- we have two different constellation
            // definitions with different numbering schemes!
            if (!justlist && (il_size(inboundstars) > 0)) {
                // This is helpful for videos: ensuring that the same
                // color is chosen for a constellation in each frame.
                int star = il_get(inboundstars, 0);
                constellations_get_star_radec(star, &ra, &dec);
                if (whitetext) {
                    r = g = b = 1;
                } else {
                    color_for_radec(ra, dec, &r, &g, &b);
                }
                // cairo_set_source_rgba(cairoshapes, r,g,b,0.8); // make all lines white
                cairo_set_source_rgba(cairoshapes, 1.0,1.0,1.0,1.0);
                cairo_set_line_width(cairoshapes, cw);
                // cairo_set_source_rgba(cairo, r,g,b,0.8); // make all lines white
                cairo_set_source_rgba(cairo, 1.0, 1.0, 1.0, 1.0);
                cairo_set_line_width(cairo, cw);
            }

            il_free(inboundstars);

            if (!sip_radec2pixelxy(&sip, label_ra, label_dec, &px, &py))
                continue;

            shortname = constellations_get_shortname(c);
            longname = constellations_get_longname(c);
            assert(shortname && longname);

            logverb("%s at (%g, %g)\n", longname, px, py);

            if (Ninbounds == Nunique) {
                printf("The constellation %s (%s)\n", longname, shortname);
            } else {
                printf("Part of the constellation %s (%s)\n", longname, shortname);
            }

            if (justlist)
                continue;

            // If the label will be off-screen, move it back on.
            cairo_text_extents(cairo, shortname, &textents);
			
            if (px < 0)
                px = 0;
            if (py < textents.height)
                py = textents.height;
            if ((px + textents.width)*scale > W)
                px = W/scale - textents.width;
            if ((py+textents.height)*scale > H)
                py = H/scale - textents.height;
            logverb("%s at (%g, %g)\n", shortname, px, py);

            cairo_set_font_size(cairos->fg, 34.0);
            add_text(cairos, longname, px, py, halign, valign);
            cairo_set_font_size(cairos->fg, 25.0);
            
            // Draw the lines.
            cairo_set_line_width(cairoshapes, lw);
            lines = constellations_get_lines(c);
            for (i=0; i<il_size(lines)/2; i++) {
                int star1, star2;
                double ra1, dec1, ra2, dec2;
                double px1, px2, py1, py2;
                double dx, dy;
                double dist;
                double gapfrac;
                star1 = il_get(lines, i*2+0);
                star2 = il_get(lines, i*2+1);
                constellations_get_star_radec(star1, &ra1, &dec1);
                constellations_get_star_radec(star2, &ra2, &dec2);
                if (!sip_radec2pixelxy(&sip, ra1, dec1, &px1, &py1) ||
                    !sip_radec2pixelxy(&sip, ra2, dec2, &px2, &py2))
                    continue;
                dx = px2 - px1;
                dy = py2 - py1;
                dist = hypot(dx, dy);
                gapfrac = endgap / dist;
                cairo_move_to(cairoshapes, px1 + dx*gapfrac, py1 + dy*gapfrac);
                cairo_line_to(cairoshapes, px1 + dx*(1.0-gapfrac), py1 + dy*(1.0-gapfrac));
                cairo_stroke(cairoshapes);
            }
            il_free(lines);
        }
        logverb("done constellations.\n");
    }

    if (custom_fn) {
        draw_custom_constellations(&thecairos, &sip, W, H, custom_fn);
    }

    if (bright) {
        double dy = 0;
        cairo_font_extents_t extents;
        pl* brightstars = pl_new(16);

        if (!justlist) {
            cairo_set_source_rgba(cairoshapes, 0.75, 0.75, 0.75, 0.8);
            cairo_font_extents(cairo, &extents);
            dy = extents.ascent * 0.5;
            cairo_set_line_width(cairoshapes, cw);
        }

        N = bright_stars_n();
        logverb("Checking %i bright stars.\n", N);

        for (i=0; i<N; i++) {
            const brightstar_t* bs = bright_stars_get(i);

            if (!sip_radec2pixelxy(&sip, bs->ra, bs->dec, &px, &py))
                continue;
            if (px < 0 || py < 0 || px*scale > W || py*scale > H)
                continue;
            if (!(bs->name && strlen(bs->name)))
                continue;
            if (common_only && !(bs->common_name && strlen(bs->common_name)))
                continue;

            if (strcmp(bs->common_name, "Maia") == 0)
                continue;

            pl_append(brightstars, bs);
        }

        // keep only the Nbright brightest?
        if (Nbright && (pl_size(brightstars) > Nbright)) {
            pl_sort(brightstars, sort_by_mag);
            pl_remove_index_range(brightstars, Nbright, pl_size(brightstars)-Nbright);
        }

        for (i=0; i<pl_size(brightstars); i++) {
            char* text;
            const brightstar_t* bs = pl_get(brightstars, i);

            if (!sip_radec2pixelxy(&sip, bs->ra, bs->dec, &px, &py))
                continue;
            if (bs->common_name && strlen(bs->common_name))
                if (print_common_only || common_only)
                    text = strdup(bs->common_name);
                else
                    asprintf_safe(&text, "%s (%s)", bs->common_name, bs->name);
            else
                text = strdup(bs->name);

            logverb("%s at (%g, %g)\n", text, px, py);

            if (json) {
                sl* names = sl_new(4);
                char* namearr;
                if (bs->common_name && strlen(bs->common_name))
                    sl_append(names, bs->common_name);
                if (bs->name)
                    sl_append(names, bs->name);
				
                namearr = sl_join(names, "\", \"");

                sl_appendf(json,
                           "{ \"type\"  : \"star\", "
                           "  \"pixelx\": %g,       "
                           "  \"pixely\": %g,       "
                           "  \"name\"  : \"%s\",   "
                           "  \"names\" : [ \"%s\" ] } "
                           , px, py,
                           (bs->common_name && strlen(bs->common_name)) ? bs->common_name : bs->name,
                           namearr);
                free(namearr);
                sl_free2(names);
            }

            if (bs->common_name && strlen(bs->common_name))
                printf("The star %s (%s)\n", bs->common_name, bs->name);
            else
                printf("The star %s\n", bs->name);

            if (!justlist) {
                float r,g,b;
                // set color based on RA,Dec to match constellations above.
                if (whitetext) {
                    r = g = b = 1;
                } else {
                    color_for_radec(bs->ra, bs->dec, &r, &g, &b);
                }
                // cairo_set_source_rgba(cairoshapes, r,g,b, 0.8); // set lines to white
                // cairo_set_source_rgba(cairo, r,g,b, 0.8); // set lines to white
                cairo_set_source_rgba(cairoshapes, 1.0, 1.0, 1.0, 1.0);
                cairo_set_source_rgba(cairo, 0.6902, 0.8784, 0.9020, 1.0);
                
            }

            if (!justlist)
                add_text(cairos, text, px + label_offset, py + dy,
                         halign, valign);

            free(text);

            if (!justlist) {
                //// plot a black circle behind the light circle...
                //cairo_arc(cairobg, px, py, crad+1.0, 0.0, 2.0*M_PI);
                //cairo_stroke(cairobg);

                //cairo_arc(cairoshapes, px, py, crad, 0.0, 2.0*M_PI);
                //cairo_stroke(cairoshapes);
            }
        }
        pl_free(brightstars);
    }

    if (NGC) {
        double imscale;
        double imsize;
        double dy = 0;
        cairo_font_extents_t extents;

        if (!justlist) {
            cairo_set_source_rgb(cairoshapes, 1.0, 1.0, 1.0);
            cairo_set_source_rgb(cairo, 1.0, 1.0, 1.0);
            cairo_set_line_width(cairo, nw);
            cairo_font_extents(cairo, &extents);
            dy = extents.ascent * 0.5;
        }

        // arcsec/pixel
        imscale = sip_pixel_scale(&sip);
        // arcmin
        imsize = imscale * (imin(W, H) / scale) / 60.0;
        N = ngc_num_entries();

        logverb("Checking %i NGC/IC objects.\n", N);

        for (i=0; i<N; i++) {
            ngc_entry* ngc = ngc_get_entry(i);
            sl* str;
            sl* names;
            double pixsize;
            char* text;
	    double tx,ty;
	    double fmargin;

            if (!ngc)
                break;
            if (ngc->size < imsize * ngc_fraction)
                continue;

            if (!sip_radec2pixelxy(&sip, ngc->ra, ngc->dec, &px, &py))
                continue;
            if (px < 0 || py < 0 || px*scale > W || py*scale > H)
                continue;

	    // Due to SIP distortions, it is possible for objects WAY outside the field to
	    // "fold" into the field.
	    // An example: /home/nova/astrometry/net/data/jobs/0700/07009522/wcs.fits
	    if (!tan_radec2pixelxy(&(sip.wcstan), ngc->ra, ngc->dec, &tx, &ty))
	      continue;
	    // margin: fraction of image size
	    fmargin = 0.1;
	    if (tx < -W*fmargin || tx*scale > (W*(1+fmargin)) ||
		ty < -H*fmargin || ty*scale > (H*(1+fmargin)))
	      continue;

            str = sl_new(4);
            //sl_appendf(str, "%s %i", (ngc->is_ngc ? "NGC" : "IC"), ngc->id);
            names = ngc_get_names(ngc, NULL);
            if (names) {
                int n;
                for (n=0; n<sl_size(names); n++) {
                    if (only_messier && strncmp(sl_get(names, n), "M ", 2))
                        continue;
                    sl_append(str, sl_get(names, n));
                }
            }
            sl_free2(names);

            text = sl_implode(str, " / ");

            printf("%s\n", text);

            pixsize = ngc->size * 60.0 / imscale;

            if (!justlist) {
                //// black circle behind the white one...
                //cairo_arc(cairobg, px, py, pixsize/2.0+1.0, 0.0, 2.0*M_PI);
                //cairo_stroke(cairobg);

                //cairo_move_to(cairoshapes, px + pixsize/2.0, py);
                //cairo_arc(cairoshapes, px, py, pixsize/2.0, 0.0, 2.0*M_PI);
                //debug("size: %f arcsec, pixsize: %f pixels\n", ngc->size, pixsize);
                //cairo_stroke(cairoshapes);

                add_text(cairos, text, px + label_offset, py + dy,
                         halign, valign);
            }

            if (json) {
                char* namelist = sl_implode(str, "\", \"");
                sl_appendf(json,
                           "{ \"type\"   : \"ngc\", "
                           "  \"names\"  : [ \"%s\" ], "
                           "  \"pixelx\" : %g, "
                           "  \"pixely\" : %g, "
                           "  \"radius\" : %g }"
                           , namelist, px, py, pixsize/2.0);
                free(namelist);
            }

            free(text);
            sl_free2(str);
        }
    }

    if (HD) {
        double rac, decc, ra2, dec2;
        double arcsec;
        hd_catalog_t* hdcat;
        bl* hdlist;
        int i;

        if (!justlist)
            cairo_set_source_rgb(cairo, 1.0, 1.0, 1.0);

        logverb("Reading HD catalog: %s\n", hdpath);
        hdcat = henry_draper_open(hdpath);
        if (!hdcat) {
            ERROR("Failed to open HD catalog");
            exit(-1);
        }
        logverb("Got %i HD stars\n", henry_draper_n(hdcat));

        sip_pixelxy2radec(&sip, W/(2.0*scale), H/(2.0*scale), &rac, &decc);
        sip_pixelxy2radec(&sip, 0.0, 0.0, &ra2, &dec2);
        arcsec = arcsec_between_radecdeg(rac, decc, ra2, dec2);
        // Fudge
        arcsec *= 1.1;
        hdlist = henry_draper_get(hdcat, rac, decc, arcsec);
        logverb("Found %zu HD stars within range (%g arcsec of RA,Dec %g,%g)\n", bl_size(hdlist), arcsec, rac, decc);

        for (i=0; i<bl_size(hdlist); i++) {
            double px, py;
            char* txt;
            hd_entry_t* hd = bl_access(hdlist, i);
            if (!sip_radec2pixelxy(&sip, hd->ra, hd->dec, &px, &py)) {
                continue;
            }
            if (px < 0 || py < 0 || px*scale > W || py*scale > H) {
                logverb("  HD %i at RA,Dec (%g, %g) -> pixel (%.1f, %.1f) is out of bounds\n",
                        hd->hd, hd->ra, hd->dec, px, py);
                continue;
            }
            asprintf_safe(&txt, "HD %i", hd->hd);
            if (!justlist) {
                cairo_text_extents_t textents;
                cairo_text_extents(cairo, txt, &textents);
                //cairo_arc(cairobg, px, py, crad+1.0, 0.0, 2.0*M_PI);
                //cairo_stroke(cairobg);
                //cairo_arc(cairoshapes, px, py, crad, 0.0, 2.0*M_PI);
                //cairo_stroke(cairoshapes);

                px -= (textents.width * 0.5);
                py -= (crad + 4.0);

                add_text(cairos, txt, px, py, halign, valign);
            }

            if (json)
                sl_appendf(json,
                           "{ \"type\"  : \"hd\","
                           "  \"pixelx\": %g, "
                           "  \"pixely\": %g, "
                           "  \"name\"  : \"HD %i\" }"
                           , px, py, hd->hd);

            printf("%s\n", txt);
            free(txt);
        }
        bl_free(hdlist);
        henry_draper_close(hdcat);
    }

    if (json) {
        FILE* fout = stderr;
        char* annstr = sl_implode(json, ",\n");
        fprintf(fout, "{ \n");
        fprintf(fout, "  \"status\": \"solved\",\n");
        fprintf(fout, "  \"git-revision\": %s,\n", AN_GIT_REVISION);
        fprintf(fout, "  \"git-date\": \"%s\",\n", AN_GIT_DATE);
        fprintf(fout, "  \"annotations\": [\n%s\n]\n", annstr);
        fprintf(fout, "}\n");
        free(annstr);
    }
    sl_free2(json);
    json = NULL;
    
    // for planets
    if (usercat_fn) {
        FILE* f = fopen(usercat_fn, "r");
        if (!f) {
            fprintf(stderr, "Failed to open user catalog file: %s\n", usercat_fn);
            exit(-1);
        }
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            char name[64];
            double ra, dec;
            if (sscanf(line, "%63s %lf %lf", name, &ra, &dec) != 3)
                continue;
            double px, py;
            if (!sip_radec2pixelxy(&sip, ra, dec, &px, &py))
                continue;
            if (px < 0 || py < 0 || px*scale > W || py*scale > H)
                continue;
            //// Draw a circle for the object
            //cairo_set_source_rgba(cairoshapes, 1.0, 1.0, 1.0, 1.0); // gold color
            //cairo_arc(cairoshapes, px, py, crad*1.5, 0.0, 2.0*M_PI);
            //cairo_stroke(cairoshapes);
            // Draw the label
            cairo_set_source_rgba(cairos->fg, 0.0, 0.0, 1.0, 1.0);
            cairo_set_font_size(cairos->fg, 31.0);
            add_text(cairos, name, px + label_offset, py, halign, valign);
            cairo_set_font_size(cairos->fg, 25.0);
            cairo_set_source_rgba(cairos->fg, 1.0, 1.0, 1.0, 1.0);
        }
        fclose(f);
    }
    
    // for other objects
    if (usercat2_fn) {
        FILE* f = fopen(usercat2_fn, "r");
        if (!f) {
            fprintf(stderr, "Failed to open user catalog file: %s\n", usercat2_fn);
            exit(-1);
        }
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            char name[64];
            double ra, dec;
            if (sscanf(line, "%63s %lf %lf", name, &ra, &dec) != 3)
                continue;
            double px, py;
            if (!sip_radec2pixelxy(&sip, ra, dec, &px, &py))
                continue;
            if (px < 0 || py < 0 || px*scale > W || py*scale > H)
                continue;
            //// Draw a circle for the object
            //cairo_set_source_rgba(cairoshapes, 1.0, 1.0, 1.0, 1.0); // gold color
            //cairo_arc(cairoshapes, px, py, crad*1.5, 0.0, 2.0*M_PI);
            //cairo_stroke(cairoshapes);
            // Draw the label
            cairo_set_source_rgba(cairos->fg, 0.6902, 0.8784, 0.9020, 1.0);
            add_text(cairos, name, px + label_offset, py, halign, valign);
            cairo_set_font_size(cairos->fg, 25.0);
            cairo_set_source_rgba(cairos->fg, 1.0, 1.0, 1.0, 1.0);

        }
        fclose(f);
    }

    if (justlist)
        return 0;

    target = cairo_image_surface_create_for_data(img, CAIRO_FORMAT_ARGB32, W, H, W*4);
    cairot = cairo_create(target);
    cairo_set_source_rgba(cairot, 0, 0, 0, 1);

    // Here's where you set the background surface's properties...
    cairo_set_source_surface(cairot, surfbg, 0, 0);
    cairo_mask_surface(cairot, surfshapesmask, 0, 0);
    cairo_stroke(cairot);

    // Add on the shapes.
    cairo_set_source_surface(cairot, surfshapes, 0, 0);
    //cairo_mask_surface(cairot, surfshapes, 0, 0);
    cairo_mask_surface(cairot, surfshapesmask, 0, 0);
    cairo_stroke(cairot);

    // Add on the foreground.
    cairo_set_source_surface(cairot, surffg, 0, 0);
    cairo_mask_surface(cairot, surffg, 0, 0);
    cairo_stroke(cairot);

    // Convert image for output...
    cairoutils_argb32_to_rgba(img, W, H);

    if (pngformat) {
        if (cairoutils_write_png(outfn, img, W, H)) {
            ERROR("Failed to write PNG");
            exit(-1);
        }
    } else {
        if (cairoutils_write_ppm(outfn, img, W, H)) {
            ERROR("Failed to write PPM");
            exit(-1);
        }
    }

    cairo_surface_destroy(target);
    cairo_surface_destroy(surfshapesmask);
    cairo_surface_destroy(surffg);
    cairo_surface_destroy(surfbg);
    cairo_surface_destroy(surfshapes);
    cairo_destroy(cairo);
    cairo_destroy(cairot);
    cairo_destroy(cairobg);
    cairo_destroy(cairoshapes);
    cairo_destroy(cairoshapesmask);
    free(img);

    return 0;
}

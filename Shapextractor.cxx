/*=====================================================================*/
/*  Scanextractor                                                      */ 
/*  based on www.sjbaker.org/wiki/index.php?title=A_Simple_3D_Scanner  */
/*=====================================================================*/


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include <string.h>

extern "C"
{
#include <jpeglib.h>
#include <jerror.h>
}

#include <math.h>

/*================================================================*/
/*    USER EDITABLE SECTION:  Change these to suit your scanner   */
/*================================================================*/
#define CAMERA_HFOV         50.0f   /* Degrees */
#define CAMERA_VFOV         (CAMERA_HFOV*4.0f/5.0f) /* Degrees */
#define CAMERA_DISTANCE     0.30f   /* Meters  */
#define LASER_OFFSET        45.0f   /* Degrees */

#define HORIZ_AVG           2 /* Num horizontal points to average */
#define VERT_AVG            2 /* Num vertical points to average */
/*================================================================*/

#define FRAME_SKIP          1  /* Use every n'th frame for speed */
#define POINT_SKIP          1  /* Use every n'th scanline for speed*/
#define RADIANS_TO_DEGREES  (180.0f / 3.14159f )
#define DEGREES_TO_RADIANS  (3.14159f / 180.0f )

class Image
{
protected:
  int width ;
  int height ;
  unsigned char *buffer ;

public:

  Image ( int w, int h )
  {
    width = w ;
    height = h ;
    buffer = new unsigned char [ w * h * 3 ] ;
  }


  Image ()
  {
    width = height = 0 ;
    buffer = NULL ;
  }


  virtual ~Image () ;

  int getWidth  () { return width  ; }
  int getHeight () { return height ; }

  unsigned char *getPixels () { return buffer ; }

  unsigned int getPixelArea ( float x1, float y1,
                              float x2, float y2,
                              unsigned int keyColour ) ;

  unsigned char getPixelRed ( int x, int y )
  {
    return (unsigned int) buffer [ ( y * width + x ) * 3 + 0 ] ;
  }

  unsigned char getPixelGreen ( int x, int y )
  {
    return (unsigned int) buffer [ ( y * width + x ) * 3 + 1 ] ;
  }

  unsigned char getPixelBlue ( int x, int y )
  {
    return (unsigned int) buffer [ ( y * width + x ) * 3 + 2 ] ;
  }

  unsigned int getPixel ( float x, float y )
  {
    return getPixel ( (int) x, (int) y ) ;
  }

  unsigned int getPixel ( int x, int y )
  {
    int p = ( y * width + x ) * 3 ;

    return ( (unsigned int) buffer [ p + 0 ] << 24 ) +
           ( (unsigned int) buffer [ p + 1 ] << 16 ) +
           ( (unsigned int) buffer [ p + 2 ] <<  8 ) + 255 ;
  }

  void setPixel ( float x, float y, unsigned int rgba )
  {
    setPixel ( (int) x, (int) y, rgba ) ;
  }

  void setPixel ( int x, int y, unsigned int rgba )
  {
    int p = ( y * width + x ) * 3 ;

    if ( ( rgba & 0xFF ) == 0 )
      return ;

    if ( ( rgba & 0xFF ) == 255 )
    {
      buffer [ p + 0 ] = ( rgba >> 24 ) & 0xFF ;
      buffer [ p + 1 ] = ( rgba >> 16 ) & 0xFF ;
      buffer [ p + 2 ] = ( rgba >>  8 ) & 0xFF ;
    }
    else
    {
      unsigned int r = ( rgba >> 24 ) & 0xFF ;
      unsigned int g = ( rgba >> 16 ) & 0xFF ;
      unsigned int b = ( rgba >>  8 ) & 0xFF ;
      unsigned int a = ( rgba >>  0 ) & 0xFF ;
      unsigned int ac = 255 - a ;

      buffer [ p + 0 ] = (unsigned char)((int)(buffer [ p + 0 ]) * ac / 255 + r * a / 255 ) ;
      buffer [ p + 1 ] = (unsigned char)((int)(buffer [ p + 1 ]) * ac / 255 + g * a / 255 ) ;
      buffer [ p + 2 ] = (unsigned char)((int)(buffer [ p + 2 ]) * ac / 255 + b * a / 255 ) ;
    }
  }

  virtual int load ( char *fname ) = 0 ;

} ;



class JPEG : public Image
{
public:

  JPEG () : Image () {}
  JPEG ( int w, int h ) : Image ( w, h ) {}

  virtual int load ( char *fname ) ;
} ;

static const int _endianTest = 1;
#define isLittleEndian (*((char *) &_endianTest ) != 0)
#define isBigEndian    (*((char *) &_endianTest ) == 0)

Image::~Image ()
{
  delete buffer ;
}


int JPEG::load ( char * filename )
{
  jpeg_decompress_struct cinfo        ;
  jpeg_error_mgr         jerr         ;

  FILE       *fd         ;
  JSAMPARRAY  linebuffer ;
  int         row_stride ;

  if ( ( fd  = fopen ( filename, "rb" ) ) == NULL )
  {
    perror  ( "readJPEG" ) ;
    fprintf ( stderr, "readJPEG: Can't open %s for reading\n", filename ) ;
    return 0 ;
  }


  cinfo.err = jpeg_std_error ( &jerr  ) ;
  jpeg_create_decompress     ( &cinfo ) ;
  jpeg_stdio_src             ( &cinfo, fd ) ;
  jpeg_read_header           ( &cinfo, TRUE ) ;
  jpeg_start_decompress      ( &cinfo ) ;

  row_stride = cinfo.output_width * cinfo.output_components ;

  if ( cinfo.output_components != 3 )
  {
    fprintf ( stderr, "readJPEG: %s has %d components?!?\n", filename,
                                       cinfo.output_components ) ;
    return 0 ;
  }

  linebuffer = (*cinfo.mem->alloc_sarray)
		      ( (j_common_ptr) &cinfo, JPOOL_IMAGE, row_stride, 1 ) ;

  delete buffer ;

  height = cinfo.output_height ;
  width  = cinfo.output_width  ;

  buffer = new unsigned char [ width * height * 3 ] ;

  while (cinfo.output_scanline < cinfo.output_height)
  {
    int y = cinfo.output_scanline ;

    /*
      jpeg_read_scanlines expects an array of pointers to scanlines.
      Here the array is only one element long, but you could ask for
      more than one scanline at a time if that's more convenient.
    */

    jpeg_read_scanlines ( &cinfo, linebuffer, 1 ) ;
    memcpy ( & buffer [ y * row_stride ], linebuffer[0], row_stride ) ;
  }

  jpeg_finish_decompress  ( &cinfo ) ;
  jpeg_destroy_decompress ( &cinfo ) ;

  fclose ( fd ) ;
  return 1 ;
}


unsigned int Image::getPixelArea ( float x1, float y1,
                                  float x2, float y2,
                                  unsigned int keyColour )
{
  if ( x2-x1 <= 0.0f || y2-y1 <= 0.0f )
    return 0x00000000 ;

  unsigned int r = ( keyColour >> 24 ) & 0xFF ;
  unsigned int g = ( keyColour >> 16 ) & 0xFF ;
  unsigned int b = ( keyColour >>  8 ) & 0xFF ;

  float area_tot = (x2-x1) * (y2-y1) ;

  float r_tot = 0.0f ;
  float g_tot = 0.0f ;
  float b_tot = 0.0f ;

  float rgb_area = 0.0f ;

  for ( int i = (int)floor(x1) ; i <= (int)ceil(x2) ; i++ )
    for ( int j = (int)floor(y1) ; j <= (int)ceil(y2) ; j++ )
    {
      if ( i < 0 || i >= width  ||
           j < 0 || j >= height ||
           getPixel( i, j ) == keyColour )
        continue ;

      float xa = ( x1 > (float)  i  ) ? x1 : (float)   i   ;
      float xb = ( x2 < (float)(i+1)) ? x2 : (float) (i+1) ;
      float ya = ( y1 > (float)  j  ) ? y1 : (float)   j   ;
      float yb = ( y2 < (float)(j+1)) ? y2 : (float) (j+1) ;

      if ( xb-xa <= 0.0f || yb-ya <= 0.0f )
        continue ;

      float area = (xb-xa) * (yb-ya) ;

      rgb_area += area ;

      r_tot += getPixelRed   ( i, j ) * area ;
      g_tot += getPixelGreen ( i, j ) * area ;
      b_tot += getPixelBlue  ( i, j ) * area ;
    }

  if ( rgb_area <= 0.0f )
    return 0x00000000 ;

  r_tot /= rgb_area ;
  g_tot /= rgb_area ;
  b_tot /= rgb_area ;

  float a_tot = rgb_area * 255.0f / area_tot ;

  if ( r_tot > 255.0f ) r_tot = 255.0f ;
  if ( g_tot > 255.0f ) g_tot = 255.0f ;
  if ( b_tot > 255.0f ) b_tot = 255.0f ;
  if ( a_tot > 255.0f ) a_tot = 255.0f ;

  if ( r_tot <= 0.0f ) r_tot = 0.0f ;
  if ( g_tot <= 0.0f ) g_tot = 0.0f ;
  if ( b_tot <= 0.0f ) b_tot = 0.0f ;
  if ( a_tot <= 0.0f ) a_tot = 0.0f ;

  return ( (unsigned int) r_tot << 24 ) +
         ( (unsigned int) g_tot << 16 ) +
         ( (unsigned int) b_tot << 8  ) +
         ( (unsigned int) a_tot << 0  ) ;
}


void ASAtoSAS ( float  angA, float  lenB, float  angC,
                float *lenA, float *angB, float *lenC )
{
  /* Find the missing angle */

  float bb = 180.0f - (angA + angC) ;

  if ( angB ) *angB = bb ;

  /* Convert everything to radians */

  angA *= DEGREES_TO_RADIANS ;
  angC *= DEGREES_TO_RADIANS ;
  bb   *= DEGREES_TO_RADIANS ;

  /* Use Sine Rule */

  float sinB = sin ( bb ) ;

  if ( sinB == 0.0f )
  {
    if ( lenA ) *lenA = lenB / 2.0f ;  /* One valid interpretation */
    if ( lenC ) *lenC = lenB / 2.0f ;
  }
  else
  {
    if ( lenA ) *lenA = lenB * sin(angA) / sinB ;
    if ( lenC ) *lenC = lenB * sin(angC) / sinB ;
  }
}


float *processRawFrame ( char *fname,char *cfname, int f, int num_frames, int *num_points )
{
  JPEG *jpg = new JPEG ;
  JPEG *jpgcolor = new JPEG ;
  float R,G,B ;
   
  jpg -> load ( fname ) ;
  jpgcolor -> load ( cfname ) ;
  int np = jpg->getHeight() / POINT_SKIP ;
  *num_points = np ; 
  
  float *res = new float [ 6 * np ] ;

  float frame_angle = ((float) f) * (360.0f / (float) num_frames) ;

  for ( int j = 0 ; j < np ; j++ )
  {
    /* Find the brightest pixel */
		R = 0.0f;
		G = 0.0f;
		B = 0.0f;
    float max  = 0.0f ;
    int maxpos = -1 ;
    for ( int i = 0 ; i < jpg -> getWidth () ; i++ )
    {
      unsigned int px = jpg -> getPixel ( i, j*POINT_SKIP ) ;

      float brightness = ((float)(( px >> 24 ) & 0xFF)) / 255.0f +
                         ((float)(( px >> 16 ) & 0xFF)) / 255.0f +
                         ((float)(( px >>  8 ) & 0xFF)) / 255.0f ;

      if ( brightness > max )
      {
        max = brightness ;
        maxpos = i ;
		
		//rgb
		unsigned int px = jpgcolor -> getPixel ( i, j*POINT_SKIP) ;
		R = ((float)(( px >> 24 ) & 0xFF))/4;
	        G = ((float)(( px >> 16 ) & 0xFF))/4;
		B = ((float)(( px >> 8 ) & 0xFF))/4;
	 }
    }

    float radius ;
    float camera_angle = CAMERA_HFOV *
                         (0.5f - (float)maxpos / (float)jpg -> getWidth ()) ;

    ASAtoSAS ( camera_angle, CAMERA_DISTANCE, LASER_OFFSET,
               & radius, NULL, NULL ) ;

    float x = radius * sin ( frame_angle * DEGREES_TO_RADIANS ) ;
    float y = radius * cos ( frame_angle * DEGREES_TO_RADIANS ) ;
    float z = atan ( (CAMERA_VFOV * DEGREES_TO_RADIANS / 2.0f) ) *
                  2.0f * CAMERA_DISTANCE * (float) j / (float) np ;

    // if ( max < 1.50 )
    //   x = y = 0.0f ;

    res [ 6 * j + 0 ] = x ;
    res [ 6 * j + 1 ] = y ;
    res [ 6 * j + 2 ] = z ;
    res [ 6 * j + 3 ] = R ;
	res [ 6 * j + 4 ] = G ;
	res [ 6 * j + 5 ] = B ;
   }
  delete jpg ;
  delete jpgcolor ;
  return res ;
}


void outputFrames ( int num_points, int num_frames, float **vertices )
{
  int num_outframes = num_frames / HORIZ_AVG ;
  int num_outpoints = num_points / VERT_AVG ;


  printf("ply\n");
  printf("format ascii 1.0\n");
  printf("comment Made with spinscan!\n");
  printf("element vertex %d\n", num_outpoints*num_outframes);
  printf("property float x\n");
  printf("property float y\n");
  printf("property float z\n");
  printf("property float nx\n");
  printf("property float ny\n");
  printf("property float nz\n");
  printf("property uchar red\n");
  printf("property uchar green\n");
  printf("property uchar blue\n");
  printf("end_header\n");
  
  for ( int f = 0 ; f < num_outframes ; f++ )
    for ( int i = 0 ; i < num_outpoints ; i++ )
    {
      float avg [ 6 ] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f } ;

      for ( int ff = 0 ; ff < HORIZ_AVG ; ff++ )
        for ( int ii = 0 ; ii < VERT_AVG ; ii++ )
        {
          avg [ 0 ] += vertices[f*HORIZ_AVG+ff][(i*VERT_AVG+ii)*6+0] ;
          avg [ 1 ] += vertices[f*HORIZ_AVG+ff][(i*VERT_AVG+ii)*6+1] ;
          avg [ 2 ] += vertices[f*HORIZ_AVG+ff][(i*VERT_AVG+ii)*6+2] ;
avg [ 3 ] += vertices[f*HORIZ_AVG+ff][(i*VERT_AVG+ii)*6+3] ;
avg [ 4 ] += vertices[f*HORIZ_AVG+ff][(i*VERT_AVG+ii)*6+4] ;
avg [ 5 ] += vertices[f*HORIZ_AVG+ff][(i*VERT_AVG+ii)*6+5] ;        
		}
      

	  avg [ 0 ] /= (float)( HORIZ_AVG*VERT_AVG ) ;
      avg [ 1 ] /= (float)( HORIZ_AVG*VERT_AVG ) ;
      avg [ 2 ] /= (float)( HORIZ_AVG*VERT_AVG ) ;

      printf ( "%f %f %f %f %f 0.000000 %i %i %i\n", avg [ 0 ], avg [ 1 ], avg [ 2 ], avg [ 0 ], avg [ 1 ], int(avg [ 3 ] ), int(avg [ 4 ] ), int(avg [ 5 ] )) ;
    }

}



int main ( int argc, char **argv )
{
  float **vertices ;

  int num_frames = 0 ;

  for ( int i = 0 ; true ; i++ )
  {
    FILE *tmp ;
    char fname [ 100 ] ;

    sprintf ( fname, "%08d.jpg", i*FRAME_SKIP ) ;

    fprintf ( stderr, "Checking %s\r", fname ) ;

    if ( (tmp = fopen ( fname, "r" )) == NULL )
      break ;

    fclose ( tmp ) ;

    num_frames = i+1 ;
  }

  fprintf ( stderr, "\nProcessing %d frames...\n", num_frames ) ;

  vertices = new float * [ num_frames ] ;

  int npoints = -1 ;

  for ( int i = 0 ; i < num_frames ; i++ )
  {
    int np ;
    char fname [ 100 ] ;
	char cfname [ 100 ] ;
    sprintf ( fname, "%08d.jpg", i*FRAME_SKIP ) ;
    sprintf ( cfname, "a%08d.jpg", i*FRAME_SKIP ) ;

    fprintf ( stderr, "Processing frame %d/%d '%s'\r",
                                          i, num_frames, fname ) ;

    vertices [ i ] = processRawFrame ( fname,cfname, i, num_frames, &np ) ;

    assert ( npoints == -1 || np == npoints ) ;

    npoints = np ;
  }

  fprintf ( stderr, "\nOutputting...\n", num_frames ) ;
  outputFrames ( npoints, num_frames, vertices ) ;
}


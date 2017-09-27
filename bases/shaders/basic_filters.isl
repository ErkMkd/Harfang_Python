in {
		tex2D u_tex; 
	
		float contrast;
		float contrast_threshold;
		float hue;
		float saturation;
		float value;
		
		float fading_level;
		vec4 fading_color;
	}

variant {
	
	vertex {
		out { vec2 v_uv; }

		source %{
			v_uv = vUV0;
			%out.position% = vec4(vPosition, 1.0);
		%}
	}

	pixel {
		in { vec2 v_uv;
				
			}

		source %{
			#define M_PI 3.14159
			#define GREY_FACTOR_R 0.11
			#define GREY_FACTOR_V 0.59
			#define GREY_FACTOR_B 0.3
			
			//-------------- Contrast filter :
			
			vec4 c;
			vec4 p=texture2D(u_tex,v_uv);			
			float c0=p.r*GREY_FACTOR_R+p.g*GREY_FACTOR_V+p.b*GREY_FACTOR_B;

			//contrast:
			c.r=clamp(p.r+contrast*(c0-contrast_threshold),0.,1.);
			c.g=clamp(p.g+contrast*(c0-contrast_threshold),0.,1.);
			c.b=clamp(p.b+contrast*(c0-contrast_threshold),0.,1.);
			c.a=1.;
			
			//--------------- Hue,Saturation,Value filter: 
			
			float VSU = value*saturation*cos(hue*M_PI/180.);
			
			float VSW = value*saturation*sin(hue*M_PI/180.);
			
			p.r = (.299*value+.701*VSU+.168*VSW)*c.r
				+ (.587*value-.587*VSU+.330*VSW)*c.g
				+ (.114*value-.114*VSU-.497*VSW)*c.b;
			p.g = (.299*value-.299*VSU-.328*VSW)*c.r
				+ (.587*value+.413*VSU+.035*VSW)*c.g
				+ (.114*value-.114*VSU+.292*VSW)*c.b;
			p.b = (.299*value-.3*VSU+1.25*VSW)*c.r
				+ (.587*value-.588*VSU-1.05*VSW)*c.g
				+ (.114*value+.886*VSU-.203*VSW)*c.b;
			
			p.a=c.a;
			
			%out.color% = p*(1-fading_level)+fading_color*fading_level;
		%}
	}
}

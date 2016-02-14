
pump_d = 24.7;
pump_D = 27.5;
wall_t = 3;
pump_h = 20;
screw_sep = 14;
screw_head_d = 8;
screw_h = 36;
slit_t = 1;

module pump(){
translate([-pump_h/2, pump_d/2 + wall_t, pump_d/2 + wall_t]) 
  rotate(a=90, v=[0, 1, 0])
  translate([0, 0, -1])
  {
    cylinder(d=pump_d, h=pump_h + 2);
    translate([0, 0, -pump_h])cylinder(d=pump_D, h=pump_h + 2);
  }
}

module p_clamp(){
  difference(){
    union(){
      difference(){
	{
	  translate([-1.25 * pump_h, pump_d/2 + wall_t, pump_d/2 + wall_t]) 
	    rotate(a=90, v=[0, 1, 0])
	    cylinder(d=pump_d + 2 * wall_t, h=2 * screw_sep + screw_head_d);
	}
	translate([1, 0, 0])pump();
      }
    
    
      difference(){
	union(){
	  for(i=[-1.5, -.5, .5]){
	    translate([i * screw_sep, -1, pump_d/5])
	      cylinder(d=screw_head_d, h=screw_h);
	  }
	}
	pump();
	cube([pump_h + 2, 100, slit_t]);
      }
    }
    // slot
    translate([-pump_h/2 - 100, -20, pump_d/2 + wall_t])
      cube([pump_h + 2 + 100, pump_d/2 + wall_t + 20, 1]);

    for(i=[-1.5, -.5, .5]){
      translate([i * screw_sep, -1, pump_d/5])
	translate([0, 0, -1])cylinder(d=4, h=screw_h+2, $fn=20);
    }
  }
}
translate([0, -pump_d/2 - wall_t, -pump_d/2 - wall_t])
color([1, 0 ,0])
p_clamp();

if(true){
  translate([1.5, 21.6, 25])
    rotate(a=180, v=[1, 0, 0])
    import("board.stl");
  
  translate([-6.5, 18, 23.5])
    rotate(a=180, v=[1, 0, 0])
    import("pump.stl");
}


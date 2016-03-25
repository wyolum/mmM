// Sensiron SF3000 inlet/outlet adapter
inletID = 19.83;
couplerID = 22.75;
couplerLength = 24;
couplerEx = 50; // coupler should extend at 5-10cm
inch = 25.4;

module coupler_tube(){
    $fn =99;
    difference(){
        cylinder(d = couplerID+2, h =couplerLength+couplerEx);
        translate([0,0,-1])cylinder(d=couplerID,h=couplerLength+1);
        translate([0,0,0])cylinder(d=inletID,h=couplerEx+couplerLength +1);
    }
}
module hose_barb(hose_id = .125*inch){
    $fn = 99;
    difference(){
        union(){
            cylinder(d=hose_id,h = .25*inch);
            translate([0,0,.25*inch])cylinder(r1 = (hose_id/2)+.5, r2 =(hose_id/2) - .5, h = .25 *inch);
            translate([0,0,.35*inch])cylinder(r1 = (hose_id/2)+.5, r2 =(hose_id/2) - .5, h = .15 *inch);
        }
        translate([0,0,-1])cylinder(d=hose_id -1, h = 1.25 *inch);
    }
} 
//hose_barb();
coupler_tube();
#!/usr/local/bin/julia

# Exoplanet orbit visualizer

# Interactive display of an exoplanet orbiting its host star
# Sliders control the orbit parameters
# Mouse controls the orientation in the screen and enables changing the viewpoint
# Use to illustrate the effect of the planets orbital parameters on observed transits

# John Kielkopf (kielkopf@louisville.edu)
# Google Gemini Pro
# MIT License
# Copyright 2026
#      
# 2021-06-06 Version 1.0


using GLMakie

function plot_orbit()
  # 1. Setup the figure and the UI layout
  fig = Figure(size = (1000, 800))

  # Create sliders for the 5 key Keplerian elements
  lsgrid = SliderGrid(fig[2, 1],
    (label = "Semimajor Axis (a)", range = 1.0:0.1:10.0, startvalue = 5.0),
    (label = "Eccentricity (e)",   range = 0.0:0.01:0.95, startvalue = 0.3),
    (label = "Inclination (i) [deg]", range = 0.0:1.0:180.0, startvalue = 45.0),
    (label = "Long. Ascending Node (Ω) [deg]", range = 0.0:1.0:360.0, startvalue = 0.0),
    (label = "Long. of Periastron (ω) [deg]", range = 0.0:1.0:360.0, startvalue = 0.0)
  )

  # Extract observables from the sliders
  a_obs = lsgrid.sliders[1].value
  e_obs = lsgrid.sliders[2].value
  i_obs = lsgrid.sliders[3].value
  Ω_obs = lsgrid.sliders[4].value
  ω_obs = lsgrid.sliders[5].value

  # Generate 200 points to draw a smooth ellipse
  ν = range(0, 2π, length=200)

  # 2. Calculate the 3D Orbit points dynamically
  # The @lift macro creates an Observable that updates whenever slider values change
  orbit_points = @lift begin
    a = $a_obs
    e = $e_obs
    i_rad = deg2rad($i_obs)
    Ω_rad = deg2rad($Ω_obs)
    ω_rad = deg2rad($ω_obs)

    pts = Point3f[]
    for nu in ν
      # Distance to the planet at true anomaly `nu`
      r = a * (1 - e^2) / (1 + e * cos(nu))

      # Coordinates in the 2D orbital plane
      x_orb = r * cos(nu)
      y_orb = r * sin(nu)

      # 3D Rotations (Z-X-Z convention)
      
      # Rotation 1: Argument of periapsis (ω) around Z-axis
      x1 = x_orb * cos(ω_rad) - y_orb * sin(ω_rad)
      y1 = x_orb * sin(ω_rad) + y_orb * cos(ω_rad)
      z1 = 0.0

      # Rotation 2: Inclination (i) around X-axis
      x2 = x1
      y2 = y1 * cos(i_rad)
      z2 = y1 * sin(i_rad)

      # Rotation 3: Longitude of ascending node (Ω) around Z-axis
      x3 = x2 * cos(Ω_rad) - y2 * sin(Ω_rad)
      y3 = x2 * sin(Ω_rad) + y2 * cos(Ω_rad)
      z3 = z2

      push!(pts, Point3f(x3, y3, z3))
    end
    pts
  end

  # 3. Draw the Scene
  ax = LScene(fig[1, 1], show_axis = true)
  
  # Draw the host star at the origin (focus of the ellipse)
  mesh!(ax, Sphere(Point3f(0, 0, 0), 0.5), color = :yellow)
  
  # Draw the dynamic orbital path
  lines!(ax, orbit_points, color = :cyan, linewidth = 3)

  # Add a reference plane (e.g., the plane of the sky)
  mesh!(ax, Rect3f(Vec3f(-12, -12, -0.05), Vec3f(24, 24, 0.1)), 
      color = (:gray, 0.2), transparency = true)

  display(fig)
end

# Run the application
plot_orbit()
println("Return to continue ...")
readline()

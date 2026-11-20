import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Sky } from "@react-three/drei";
import { CapsuleCollider, CuboidCollider, Physics, RigidBody } from "@react-three/rapier";
import * as THREE from "three";
import { createLabelTexture } from "./labelTexture.js";

const BUILDING_COLORS = ["#b1d5ca", "#d9c8a9", "#b5cbe0", "#e5c4ad", "#d8d0b1", "#d2bfda", "#d3c4a8", "#c5c6df"];

function createCampusBuildings(subjects) {
  const entries = [
    { id: "library", name: "THE LIBRARY", subtitle: "Read • Imagine • Explore", color: "#d8d0b1" },
    ...subjects.map((subject, index) => ({
      id: subject.slug,
      name: subject.building.toUpperCase(),
      subtitle: subject.name,
      color: BUILDING_COLORS[index % BUILDING_COLORS.length],
    })),
  ];
  const columns = 5;
  const rows = Math.ceil(entries.length / columns);
  return entries.map((entry, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    return {
      ...entry,
      position: [(column - (columns - 1) / 2) * 11, 0, (row - (rows - 1) / 2) * 10],
      width: 6.4,
      depth: 4.8,
    };
  });
}

const TREE_POSITIONS = [
  [-18, -12], [-16, 2], [-17, 15], [-3, -17], [9, -17], [18, -11],
  [18, 3], [18, 17], [-16, 19], [4, 17], [14, 14], [-12, 12],
];

function Building({ building }) {
  const w = building.width;
  const d = building.depth;
  const labelTexture = useMemo(
    () => createLabelTexture(building.name, building.subtitle),
    [building.name, building.subtitle],
  );
  useEffect(() => () => labelTexture.dispose(), [labelTexture]);
  return (
    <group position={building.position}>
      <mesh position={[0, 0.12, 0]} receiveShadow>
        <boxGeometry args={[w + 1.2, 0.24, d + 1.2]} />
        <meshStandardMaterial color="#c6d1c9" roughness={0.92} />
      </mesh>
      <mesh position={[0, 1.8, 0]} castShadow receiveShadow>
        <boxGeometry args={[w, 3.3, d]} />
        <meshStandardMaterial color={building.color} roughness={0.8} />
      </mesh>
      <mesh position={[0, 3.52, 0]} castShadow>
        <boxGeometry args={[w + 0.35, 0.22, d + 0.35]} />
        <meshStandardMaterial color="#314c55" roughness={0.72} />
      </mesh>
      <mesh position={[0, 0.91, d / 2 + 0.02]} castShadow>
        <boxGeometry args={[1.15, 1.8, 0.12]} />
        <meshStandardMaterial color="#31505a" roughness={0.45} />
      </mesh>
      {[-1, 1].map((side) => (
        <mesh key={side} position={[side * w * 0.32, 2.13, d / 2 + 0.035]}>
          <boxGeometry args={[1.1, 0.94, 0.09]} />
          <meshStandardMaterial color="#90c4c4" emissive="#366b70" emissiveIntensity={0.12} />
        </mesh>
      ))}
      <mesh position={[0, 3.88, d / 2 + 0.18]}>
        <boxGeometry args={[w * 0.8, 0.68, 0.14]} />
        <meshStandardMaterial map={labelTexture} roughness={0.85} />
      </mesh>
      <mesh position={[0, 0.03, d / 2 + 1.8]} receiveShadow>
        <boxGeometry args={[w + 1.8, 0.04, 2.6]} />
        <meshStandardMaterial color="#ded9cc" roughness={0.95} />
      </mesh>
    </group>
  );
}

function Tree({ position, scale = 1 }) {
  return (
    <group position={[position[0], 0, position[1]]} scale={scale}>
      <mesh position={[0, 0.85, 0]} castShadow>
        <cylinderGeometry args={[0.16, 0.25, 1.7, 7]} />
        <meshStandardMaterial color="#80634b" roughness={1} />
      </mesh>
      <mesh position={[0, 2.03, 0]} castShadow>
        <icosahedronGeometry args={[1.02, 1]} />
        <meshStandardMaterial color="#557b5d" roughness={1} />
      </mesh>
      <mesh position={[0.5, 2.26, 0.15]} castShadow>
        <icosahedronGeometry args={[0.58, 1]} />
        <meshStandardMaterial color="#6e946b" roughness={1} />
      </mesh>
    </group>
  );
}

function Bench({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.55, 0]} castShadow>
        <boxGeometry args={[1.8, 0.12, 0.48]} />
        <meshStandardMaterial color="#9b7455" />
      </mesh>
      <mesh position={[0, 0.9, -0.18]} castShadow>
        <boxGeometry args={[1.8, 0.62, 0.12]} />
        <meshStandardMaterial color="#9b7455" />
      </mesh>
      {[-0.65, 0.65].map((x) => (
        <mesh key={x} position={[x, 0.28, 0]} castShadow>
          <boxGeometry args={[0.12, 0.56, 0.38]} />
          <meshStandardMaterial color="#465b55" />
        </mesh>
      ))}
    </group>
  );
}

function AvatarModel({ moving, running }) {
  const leftArm = useRef();
  const rightArm = useRef();
  const leftLeg = useRef();
  const rightLeg = useRef();
  useFrame(({ clock }) => {
    const swing = moving ? Math.sin(clock.elapsedTime * (running ? 12 : 8)) * (running ? 0.54 : 0.36) : 0;
    if (leftArm.current) leftArm.current.rotation.x = swing;
    if (rightArm.current) rightArm.current.rotation.x = -swing;
    if (leftLeg.current) leftLeg.current.rotation.x = -swing;
    if (rightLeg.current) rightLeg.current.rotation.x = swing;
  });

  return (
    <group>
      <mesh position={[0, 1.32, 0]} castShadow>
        <capsuleGeometry args={[0.37, 0.64, 5, 10]} />
        <meshStandardMaterial color="#e1a66f" roughness={0.8} />
      </mesh>
      <mesh position={[0, 1.55, 0.035]} castShadow>
        <boxGeometry args={[0.72, 0.78, 0.4]} />
        <meshStandardMaterial color="#477b79" roughness={0.75} />
      </mesh>
      <mesh position={[0, 2.13, 0]} castShadow>
        <sphereGeometry args={[0.33, 18, 16]} />
        <meshStandardMaterial color="#dca579" roughness={0.82} />
      </mesh>
      <mesh position={[0, 2.32, -0.025]} castShadow>
        <sphereGeometry args={[0.34, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.47]} />
        <meshStandardMaterial color="#3c302b" roughness={0.98} />
      </mesh>
      {[-1, 1].map((side) => (
        <group key={side} ref={side < 0 ? leftArm : rightArm} position={[side * 0.48, 1.79, 0]}>
          <mesh position={[0, -0.24, 0]} castShadow>
            <capsuleGeometry args={[0.12, 0.38, 4, 8]} />
            <meshStandardMaterial color="#477b79" roughness={0.8} />
          </mesh>
        </group>
      ))}
      {[-1, 1].map((side) => (
        <group key={side} ref={side < 0 ? leftLeg : rightLeg} position={[side * 0.19, 0.84, 0]}>
          <mesh position={[0, -0.34, 0]} castShadow>
            <capsuleGeometry args={[0.14, 0.5, 4, 8]} />
            <meshStandardMaterial color="#374a58" roughness={0.88} />
          </mesh>
        </group>
      ))}
      <mesh position={[0, 2.13, 0.29]}>
        <sphereGeometry args={[0.025, 8, 8]} />
        <meshStandardMaterial color="#25323a" />
      </mesh>
    </group>
  );
}

function Player({ buildings, onNearBuilding, onInteract, paused }) {
  const body = useRef();
  const visual = useRef();
  const controls = useRef();
  const keys = useRef(new Set());
  const { camera } = useThree();
  const moveDirection = useRef(new THREE.Vector3());
  const forward = useRef(new THREE.Vector3());
  const right = useRef(new THREE.Vector3());
  const lastProximityUpdate = useRef(0);
  const previousMoving = useRef(false);
  const previousRunning = useRef(false);
  const previousNearBuilding = useRef(null);
  const [moving, setMoving] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const down = (event) => {
      if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.code)) event.preventDefault();
      keys.current.add(event.code);
      if (event.code === "KeyE" && !paused) onInteract();
    };
    const up = (event) => keys.current.delete(event.code);
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [onInteract, paused]);

  useFrame((state, delta) => {
    if (!body.current) return;
    const position = body.current.translation();
    const velocity = body.current.linvel();
    const input = keys.current;
    const forwardInput = Number(input.has("KeyW") || input.has("ArrowUp")) - Number(input.has("KeyS") || input.has("ArrowDown"));
    const sideInput = Number(input.has("KeyD") || input.has("ArrowRight")) - Number(input.has("KeyA") || input.has("ArrowLeft"));
    const isRunning = input.has("ShiftLeft") || input.has("ShiftRight");
    forward.current.set(0, 0, -1).applyQuaternion(camera.quaternion);
    forward.current.y = 0;
    forward.current.normalize();
    right.current.set(-forward.current.z, 0, forward.current.x);
    moveDirection.current.set(0, 0, 0)
      .addScaledVector(forward.current, forwardInput)
      .addScaledVector(right.current, sideInput);
    if (moveDirection.current.lengthSq() > 0) moveDirection.current.normalize();
    const isMoving = moveDirection.current.lengthSq() > 0;
    const speed = isRunning ? 7.1 : 4.3;
    if (!paused) {
      body.current.setLinvel({
        x: moveDirection.current.x * speed,
        y: velocity.y,
        z: moveDirection.current.z * speed,
      }, true);
      if (input.has("Space") && position.y < 1.3 && velocity.y < 0.5) {
        body.current.setLinvel({ x: velocity.x, y: 5.2, z: velocity.z }, true);
        input.delete("Space");
      }
    } else {
      body.current.setLinvel({ x: 0, y: velocity.y, z: 0 }, true);
    }

    if (!paused && isMoving && visual.current) {
      visual.current.rotation.y = Math.atan2(moveDirection.current.x, moveDirection.current.z);
    }
    if (visual.current) {
        visual.current.position.y = -0.9 + (!paused && isMoving
          ? Math.abs(Math.sin(state.clock.elapsedTime * 9)) * 0.035
          : Math.sin(state.clock.elapsedTime * 1.8) * 0.025);
    }
    const shouldMove = !paused && isMoving;
    if (previousMoving.current !== shouldMove) {
      previousMoving.current = shouldMove;
      setMoving(shouldMove);
    }
    if (previousRunning.current !== isRunning) {
      previousRunning.current = isRunning;
      setRunning(isRunning);
    }
    controls.current?.target.set(position.x, position.y + 1.2, position.z);
    controls.current?.update();
    if (state.clock.elapsedTime - lastProximityUpdate.current > 0.18) {
      const nearest = buildings
        .map((building) => ({
          building,
          distance: Math.hypot(
            position.x - building.position[0],
            position.z - (building.position[2] + building.depth / 2 + 1.8),
          ),
        }))
        .sort((a, b) => a.distance - b.distance)[0];
      const currentBuilding = nearest && nearest.distance < 4.3 ? nearest.building : null;
      const currentId = currentBuilding?.id || null;
      if (previousNearBuilding.current !== currentId) {
        previousNearBuilding.current = currentId;
        onNearBuilding(currentBuilding);
      }
      lastProximityUpdate.current = state.clock.elapsedTime;
    }
  });

  return (
    <>
      <OrbitControls
        ref={controls}
        makeDefault
        target={[0, 1.2, 8]}
        enablePan={false}
        enableDamping
        dampingFactor={0.09}
        minDistance={5}
        maxDistance={13}
        minPolarAngle={0.26}
        maxPolarAngle={1.42}
      />
      <RigidBody
        ref={body}
        colliders={false}
        position={[0, 0.9, 8]}
        enabledRotations={[false, false, false]}
        linearDamping={0.9}
        angularDamping={1}
        mass={1}
        userData={{ player: true }}
      >
        <CapsuleCollider args={[0.52, 0.34]} />
        <group ref={visual} position={[0, -0.9, 0]}>
          <AvatarModel moving={moving && !paused} running={running} />
        </group>
      </RigidBody>
    </>
  );
}

function CampusEnvironment({ buildings }) {
  const campusSign = useMemo(
    () => createLabelTexture("EDUPLAY", "LEARN BY EXPLORING", "#38574e"),
    [],
  );
  useEffect(() => () => campusSign.dispose(), [campusSign]);
  return (
    <>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.12, 0]} receiveShadow>
        <planeGeometry args={[72, 72]} />
        <meshStandardMaterial color="#91a88b" roughness={1} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.095, 0]} receiveShadow>
        <planeGeometry args={[4.2, 64]} />
        <meshStandardMaterial color="#d6cebb" roughness={0.92} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.09, 0]} receiveShadow>
        <planeGeometry args={[64, 4.2]} />
        <meshStandardMaterial color="#d6cebb" roughness={0.92} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.075, 0]} receiveShadow>
        <circleGeometry args={[4.2, 48]} />
        <meshStandardMaterial color="#e4dcc7" roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.01, 0]} receiveShadow>
        <cylinderGeometry args={[2.45, 2.45, 0.08, 32]} />
        <meshStandardMaterial color="#a8b99a" roughness={0.9} />
      </mesh>
      {buildings.map((building) => <Building key={building.id} building={building} />)}
      {TREE_POSITIONS.map((position, index) => (
        <Tree key={`${position[0]}-${position[1]}`} position={position} scale={0.78 + (index % 3) * 0.12} />
      ))}
      <Bench position={[-3.4, 0, 3.4]} />
      <Bench position={[4.2, 0, 3.4]} />
      <mesh position={[0, 1.35, -3.2]} castShadow>
        <boxGeometry args={[3.8, 2.7, 0.22]} />
        <meshStandardMaterial color="#8b7559" />
      </mesh>
      <mesh position={[0, 2.8, -3.19]}>
        <boxGeometry args={[3.8, 0.18, 0.26]} />
        <meshStandardMaterial color="#e4b46e" />
      </mesh>
      <mesh position={[0, 1.45, -3.05]}>
        <planeGeometry args={[3.6, 1.25]} />
        <meshStandardMaterial map={campusSign} />
      </mesh>
    </>
  );
}

export default function GameWorld({ subjects = [], onNearBuilding, onInteract, paused }) {
  const buildings = createCampusBuildings(subjects);
  const interact = useCallback(() => onInteract(), [onInteract]);
  return (
    <Canvas shadows camera={{ position: [0, 7, 15], fov: 47 }} dpr={[1, 1.6]} gl={{ antialias: true, powerPreference: "high-performance" }}>
      <color attach="background" args={["#a9c5cc"]} />
      <fog attach="fog" args={["#a9c5cc", 28, 72]} />
      <Sky sunPosition={[40, 35, -30]} turbidity={7} rayleigh={1.2} />
      <ambientLight intensity={0.9} />
      <directionalLight position={[12, 22, 8]} intensity={2.2} castShadow shadow-mapSize={[1024, 1024]} shadow-camera-far={60} shadow-camera-left={-28} shadow-camera-right={28} shadow-camera-top={28} shadow-camera-bottom={-28} />
      <Physics gravity={[0, -18, 0]}>
        <CampusEnvironment buildings={buildings} />
        <RigidBody type="fixed" colliders={false}>
          <CuboidCollider position={[0, -0.23, 0]} args={[36, 0.12, 36]} />
          {buildings.map((building) => (
            <CuboidCollider
              key={building.id}
              position={[building.position[0], 1.7, building.position[2]]}
              args={[building.width / 2, 1.65, building.depth / 2]}
            />
          ))}
        </RigidBody>
        <Player buildings={buildings} onNearBuilding={onNearBuilding} onInteract={interact} paused={paused} />
      </Physics>
    </Canvas>
  );
}


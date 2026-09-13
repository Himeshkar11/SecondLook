import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

/**
 * Hero3D — SecondLook 3D Hero Experience
 * Concept: "Evidence & Compliance Inspection Constellation"
 * 
 * Features:
 * - Central rotating faceted Inspection Gateway with national tricolor accents
 * - Floating orbital document cards representing Tender, Bid, GST, and Compliance evidence
 * - Connecting evidence lines & statutory verification nodes
 * - Smooth mouse parallax tilt interaction
 * - IntersectionObserver to halt rendering when out of viewport
 * - Respects prefers-reduced-motion
 * - Comprehensive WebGL error handling & elegant SVG fallback
 */
export default function Hero3D() {
  const containerRef = useRef(null);
  const [webGlAvailable, setWebGlAvailable] = useState(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Detect WebGL support
    let isSupported = false;
    try {
      const testCanvas = document.createElement('canvas');
      isSupported = Boolean(
        window.WebGLRenderingContext &&
          (testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl'))
      );
    } catch {
      isSupported = false;
    }

    if (!isSupported) {
      setWebGlAvailable(false);
      return;
    }

    // 2. Reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // 3. Scene, Camera, Renderer Setup
    const width = container.clientWidth || 540;
    const height = container.clientHeight || 480;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 14);

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);
      container.appendChild(renderer.domElement);
    } catch {
      setWebGlAvailable(false);
      return;
    }

    // Master Group for mouse parallax
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x1e4e8c, 2.5, 30);
    pointLight1.position.set(6, 6, 8);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xd97706, 2.0, 30);
    pointLight2.position.set(-6, -5, 6);
    scene.add(pointLight2);

    const pointLight3 = new THREE.PointLight(0x138808, 1.8, 30);
    pointLight3.position.set(0, 7, -4);
    scene.add(pointLight3);

    // 5. Central Inspection Gateway Core (Faceted Hexagonal Geometry)
    const coreGeo = new THREE.CylinderGeometry(2.0, 2.0, 0.75, 6);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x1e3a8a,
      roughness: 0.25,
      metalness: 0.85,
      wireframe: false,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreMesh.rotation.x = Math.PI / 6;
    mainGroup.add(coreMesh);

    // Core Wireframe overlay
    const coreWireMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const coreWireMesh = new THREE.Mesh(coreGeo, coreWireMat);
    coreMesh.add(coreWireMesh);

    // Tricolor Accent Rings surrounding Core
    const ringGeo1 = new THREE.TorusGeometry(2.8, 0.04, 16, 64);
    const ringMatSaffron = new THREE.MeshBasicMaterial({ color: 0xff9933, transparent: true, opacity: 0.85 });
    const ring1 = new THREE.Mesh(ringGeo1, ringMatSaffron);
    ring1.rotation.x = Math.PI / 3;
    mainGroup.add(ring1);

    const ringGeo2 = new THREE.TorusGeometry(3.2, 0.035, 16, 64);
    const ringMatWhite = new THREE.MeshBasicMaterial({ color: 0xe2e8f0, transparent: true, opacity: 0.7 });
    const ring2 = new THREE.Mesh(ringGeo2, ringMatWhite);
    ring2.rotation.y = Math.PI / 4;
    mainGroup.add(ring2);

    const ringGeo3 = new THREE.TorusGeometry(3.6, 0.04, 16, 64);
    const ringMatGreen = new THREE.MeshBasicMaterial({ color: 0x138808, transparent: true, opacity: 0.85 });
    const ring3 = new THREE.Mesh(ringGeo3, ringMatGreen);
    ring3.rotation.z = Math.PI / 5;
    mainGroup.add(ring3);

    // 6. Orbital Floating Document & Evidence Nodes
    const documentCards = [];
    const cardData = [
      { color: 0x3b82f6, pos: [-4.2, 2.0, 1.2], label: 'Tender' },
      { color: 0x10b981, pos: [4.2, 1.5, 0.8], label: 'GSTIN Verified' },
      { color: 0xf59e0b, pos: [-3.4, -2.4, 1.6], label: 'PAN Validated' },
      { color: 0x6366f1, pos: [3.6, -2.0, 1.4], label: 'Compliance Audit' },
      { color: 0x14b8a6, pos: [0.0, 3.8, -1.0], label: 'Statutory Evidence' },
    ];

    const cardGeo = new THREE.BoxGeometry(1.6, 1.0, 0.08);

    cardData.forEach((data, index) => {
      const cardMat = new THREE.MeshStandardMaterial({
        color: data.color,
        metalness: 0.4,
        roughness: 0.3,
        transparent: true,
        opacity: 0.88,
      });
      const card = new THREE.Mesh(cardGeo, cardMat);
      card.position.set(data.pos[0], data.pos[1], data.pos[2]);
      card.rotation.z = (index % 2 === 0 ? 1 : -1) * 0.15;
      mainGroup.add(card);

      // Card border highlight
      const borderGeo = new THREE.EdgesGeometry(cardGeo);
      const borderMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 });
      const border = new THREE.LineSegments(borderGeo, borderMat);
      card.add(border);

      // Evidence Connecting Line to Core
      const points = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(data.pos[0], data.pos[1], data.pos[2])];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineDashedMaterial({
        color: data.color,
        dashSize: 0.2,
        gapSize: 0.1,
        transparent: true,
        opacity: 0.45,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      line.computeLineDistances();
      mainGroup.add(line);

      documentCards.push({ mesh: card, initialPos: [...data.pos], phase: index * 1.3 });
    });

    // 7. Ambient Statutory Verification Node Particles
    const particleCount = 48;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 16;
      particlePositions[i + 1] = (Math.random() - 0.5) * 12;
      particlePositions[i + 2] = (Math.random() - 0.5) * 8;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x93c5fd,
      size: 0.12,
      transparent: true,
      opacity: 0.65,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    mainGroup.add(particles);

    // 8. Mouse Parallax Handlers
    let targetRotX = 0;
    let targetRotY = 0;

    const handleMouseMove = (e) => {
      if (prefersReducedMotion) return;
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetRotY = x * 0.35;
      targetRotX = -y * 0.25;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    // 9. Resize Handling
    const handleResize = () => {
      if (!container || !renderer) return;
      const newWidth = container.clientWidth || 540;
      const newHeight = container.clientHeight || 480;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // 10. IntersectionObserver to pause when off-screen
    let isVisible = true;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          isVisible = entry.isIntersecting;
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(container);

    // 11. Animation Loop
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      if (!isVisible) return;

      const elapsedTime = clock.getElapsedTime();

      if (!prefersReducedMotion) {
        // Slow core rotation
        coreMesh.rotation.y = elapsedTime * 0.35;
        coreMesh.rotation.x = Math.PI / 6 + Math.sin(elapsedTime * 0.5) * 0.1;

        // Counter-rotating tricolor orbital rings
        ring1.rotation.z = elapsedTime * 0.25;
        ring2.rotation.x = elapsedTime * -0.2;
        ring3.rotation.y = elapsedTime * 0.18;

        // Floating hover motion for document cards
        documentCards.forEach((item) => {
          item.mesh.position.y = item.initialPos[1] + Math.sin(elapsedTime * 1.4 + item.phase) * 0.22;
          item.mesh.position.x = item.initialPos[0] + Math.cos(elapsedTime * 0.8 + item.phase) * 0.12;
        });

        // Ambient particles slow drift
        particles.rotation.y = elapsedTime * 0.05;

        // Smooth mouse parallax lerp
        mainGroup.rotation.y += (targetRotY - mainGroup.rotation.y) * 0.05;
        mainGroup.rotation.x += (targetRotX - mainGroup.rotation.x) * 0.05;
      }

      renderer.render(scene, camera);
    };

    animate();

    // 12. Complete Resource Cleanup on Unmount
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      observer.disconnect();

      if (renderer && renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }

      // Geometries
      coreGeo.dispose();
      ringGeo1.dispose();
      ringGeo2.dispose();
      ringGeo3.dispose();
      cardGeo.dispose();
      particleGeo.dispose();

      // Materials
      coreMat.dispose();
      coreWireMat.dispose();
      ringMatSaffron.dispose();
      ringMatWhite.dispose();
      ringMatGreen.dispose();
      particleMat.dispose();

      if (renderer) {
        renderer.dispose();
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: '440px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      aria-label="Interactive 3D Evidence & Compliance Inspection Constellation"
      role="region"
    >
      {/* Graceful Fallback if WebGL is disabled or unsupported */}
      {!webGlAvailable && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--space-6)',
            textAlign: 'center',
            background: 'radial-gradient(circle, var(--color-primary-subtle) 0%, transparent 70%)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border)',
            maxWidth: '420px',
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: 'var(--space-2)' }}>🏛️⚖️🛡️</div>
          <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--color-primary)' }}>
            Evidence &amp; Verification Architecture
          </h4>
          <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
            Automated statutory cross-referencing for GSTIN, PAN, and technical bid specifications backed by deterministic compliance evaluation.
          </p>
        </div>
      )}
    </div>
  );
}

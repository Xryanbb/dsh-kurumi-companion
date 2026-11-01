#!/usr/bin/env node
// Local selector for QCYTSN/dsh-dafeiyu's optional custom macOS skin support.
// Does not build the helper, stop DSH, or access any credentials.
import { copyFileSync, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const args = process.argv.slice(2)
if (args.some((arg) => arg !== '--dry-run')) {
  throw new Error('Usage: node install-skin.mjs [--dry-run]')
}
const skinRoot = dirname(fileURLToPath(import.meta.url))
const source = join(skinRoot, 'images')
const approvedIdleSource = join(skinRoot, '../kurumi-animation/reference/idle-approved.png')
const happyFrameSource = join(skinRoot, 'animations', 'happy')
const headPatFrameSource = join(skinRoot, 'animations', 'head_pat')
const pokeFrameSource = join(skinRoot, 'animations', 'poke')
const hairRibbonFrameSource = join(skinRoot, 'animations', 'hair_ribbon_v3')
const dshHome = resolve(process.env.DSH_HOME || join(homedir(), '.dsh'))
const directory = join(dshHome, 'dsh-dafeiyu')
const target = join(directory, 'skins', 'kurumi-animated-v3')
const happyFrameTarget = join(target, 'animations', 'happy-wave-v1')
const headPatFrameTarget = join(target, 'animations', 'head-pat-v1')
const pokeFrameTarget = join(target, 'animations', 'poke-v1')
const hairRibbonFrameTarget = join(target, 'animations', 'hair-ribbon-v2')
const greetingFrameSource = join(skinRoot, '../kurumi-animation/generated')
const greetingFrameTarget = join(target, 'animations', 'greeting-wave-v1')
const selectionPath = join(directory, 'skin.json')
const names = ['idle', 'idle-blink', 'thought', 'working', 'happy', 'dragging']
const images = Object.fromEntries(names.map((name) => [name, join(target, `${name}.png`)]))
const happyFrameNames = Array.from({ length: 9 }, (_, index) => `frame-${String(index + 1).padStart(3, '0')}.png`)
const happyFrameSources = happyFrameNames.map((name) => join(happyFrameSource, name))
const happyFramePaths = happyFrameNames.map((name) => join(happyFrameTarget, name))
const headPatFrameNames = happyFrameNames
const headPatFrameSources = headPatFrameNames.map((name) => join(headPatFrameSource, name))
const headPatFramePaths = headPatFrameNames.map((name) => join(headPatFrameTarget, name))
const pokeFrameNames = Array.from({ length: 8 }, (_, index) => `frame-${String(index + 1).padStart(3, '0')}.png`)
const pokeFrameSources = pokeFrameNames.map((name) => join(pokeFrameSource, name))
const pokeFramePaths = pokeFrameNames.map((name) => join(pokeFrameTarget, name))
const hairRibbonFrameNames = Array.from({ length: 9 }, (_, index) => `frame-${String(index + 1).padStart(3, '0')}.png`)
const hairRibbonFrameSources = hairRibbonFrameNames.map((name) => join(hairRibbonFrameSource, name))
const hairRibbonFramePaths = hairRibbonFrameNames.map((name) => join(hairRibbonFrameTarget, name))
const greetingFrameNames = [
  'wave-start-v1.png',
  'wave-anticipation-v1.png',
  'wave-intermediate-v1.png',
  'wave-intermediate-v2.png',
  'wave-recovery-v1.png',
  'wave-lowered-v1.png',
]
const greetingFrameSources = greetingFrameNames.map((name) => join(greetingFrameSource, name))
const greetingFramePaths = greetingFrameNames.map((name) => join(greetingFrameTarget, name))

// Validate all inputs before creating any user-directory files.
for (const path of [
  ...names.map((name) => join(source, `${name}.png`)),
  approvedIdleSource,
  ...happyFrameSources,
  ...headPatFrameSources, ...pokeFrameSources, ...hairRibbonFrameSources, ...greetingFrameSources,
]) {
  const bytes = readFileSync(path)
  if (bytes.length < 8 || !bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    throw new Error(`Invalid PNG: ${path}`)
  }
}
const selection = {
  imagePath: images.idle,
  name: '时崎狂三',
  states: {
    IDLE: images.idle,
    THINKING: images.thought,
    WORKING: images.working,
    SUCCESS: images.idle,
    WAITING: images.thought,
    ERROR: images.thought,
  },
  interactionImagePath: images.happy,
  draggingImagePath: images.dragging,
  blinkImagePath: images['idle-blink'],
  frameSequences: {
    SUCCESS: {
      enter: [images.idle, greetingFramePaths[0]],
      body: [greetingFramePaths[1], greetingFramePaths[2], greetingFramePaths[3], greetingFramePaths[2]],
      exit: [greetingFramePaths[4], greetingFramePaths[0], greetingFramePaths[5], images.idle],
      frameMs: 120,
      loop: false,
      interpolate: true,
      blendFrames: true,
      interpolationWindow: 0.45,
      normalizeToSkinScale: true,
    },
    INTERACTION_HEAD_PAT: { frames: headPatFramePaths, frameMs: 120, loop: false, blendFrames: true },
    INTERACTION_POKE: { frames: pokeFramePaths, frameMs: 120, loop: false, blendFrames: true },
    INTERACTION_HAIR_RIBBON: { frames: hairRibbonFramePaths, frameMs: 180, loop: false, blendFrames: true, normalizeToSkinScale: true },
  },
}
if (args.includes('--dry-run')) {
  console.log(JSON.stringify({ dryRun: true, selectionPath, imageDirectory: target, selection }, null, 2))
} else {
  mkdirSync(target, { recursive: true, mode: 0o700 })
  for (const name of names) {
    const temporary = `${images[name]}.tmp-${process.pid}`
    copyFileSync(name === 'idle' ? approvedIdleSource : join(source, `${name}.png`), temporary)
    renameSync(temporary, images[name])
  }
  for (const sequence of [
    { target: happyFrameTarget, names: happyFrameNames, sources: happyFrameSources, paths: happyFramePaths },
    { target: headPatFrameTarget, names: headPatFrameNames, sources: headPatFrameSources, paths: headPatFramePaths },
    { target: pokeFrameTarget, names: pokeFrameNames, sources: pokeFrameSources, paths: pokeFramePaths },
    { target: hairRibbonFrameTarget, names: hairRibbonFrameNames, sources: hairRibbonFrameSources, paths: hairRibbonFramePaths },
    { target: greetingFrameTarget, names: greetingFrameNames, sources: greetingFrameSources, paths: greetingFramePaths },
  ]) {
    mkdirSync(sequence.target, { recursive: true, mode: 0o700 })
    for (let index = 0; index < sequence.names.length; index += 1) {
      const temporary = `${sequence.paths[index]}.tmp-${process.pid}`
      copyFileSync(sequence.sources[index], temporary)
      renameSync(temporary, sequence.paths[index])
    }
  }
  if (existsSync(selectionPath)) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-')
    copyFileSync(selectionPath, `${selectionPath}.backup-${stamp}`)
  }
  const temporary = `${selectionPath}.tmp-${process.pid}`
  writeFileSync(temporary, JSON.stringify(selection, null, 2) + '\n', { mode: 0o600 })
  renameSync(temporary, selectionPath)
  console.log(`Kurumi skin selected: ${selectionPath}`)
  console.log('Restart the DSH Host with this branch’s custom-skin macOS Helper to apply it.')
}

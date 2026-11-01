# 狂三面部与发丝纹理 v2

使用内置 imagegen，根据用户选定的现用狂三同人皮肤生成。未复制大肥鱼角色图片。角色权利归《约会大作战》相应权利人；本分支不宣称角色原创。

参考原图 SHA-256：0679fb64aa9f9bc97e2a8dccee7ce904d534d1fe700391aa8f41499d8b453761。

face.png 用于真实头部曲面的投影 UV；hair.png 用于真实发束曲面的 UV。两张图都不是替代整个人物的平面精灵。当前面部纹理尚未制作眨眼形变，不属于动画完成版。

## 面部提示词

Use case: identity-preserve. Asset type: a flat front-projected face albedo texture for a real 3D chibi anime mesh, not a portrait. Reference image is the currently approved Kurumi desktop pet. Preserve its detailed soft anime painting, ruby red viewer-left eye, warm amber clock viewer-right eye, delicate eyelash silhouette and gentle mischievous smile. Generate ONLY facial features painted on a completely uniform pale peach skin color filling the entire square canvas edge to edge (#fff0e5). NO head outline, NO hair, NO ears, NO neck, NO clothing, NO border, NO text, NO cast shadow. The face is horizontally centered and perfectly front-on. Large detailed almond anime eyes at horizontal 29% and 71%, eye-center vertical 57% from top; each eye occupies roughly 26% of canvas width and 20% height. Eye highlights, layered translucent irises and fine iris texture must match reference quality; upper lashes naturally curved, no angry slant, no staring circles. Tiny subtle nose at 50%,69%, a very small curved smile centered at 50%,78%, subtle translucent blush at 22%,72% and 78%,72%. Delicate brows above eyes. The upper 35% and outer edges remain uniform skin color, since a separate 3D fringe and head mesh cover them. Flat unlit texture, no ambient occlusion or 3D face shading. One square texture only.

## 发丝提示词

Use case: stylized-concept. Asset type: seamless-width painted anime hair albedo texture for curved 3D hair locks. Reference is the approved Kurumi pet. Fill the ENTIRE square canvas with a continuous dark charcoal brown-black hair surface, no character, no face, no head shape, no silhouette, no transparency, no text. Hair fibers run vertically top to bottom. Sophisticated soft anime shading matching reference's hair: many fine dark strands, subtle warm mauve-gray narrow highlights, uneven organically grouped fine locks. Broad soft low-contrast painted reflection band around upper third, less bright than dark gray; most canvas nearly black brown #30272c. No white highlights, no metallic chrome shine, no geometric shapes. Uniform dark vertical edges suitable for wrapping around ribbon hair meshes, constant dark top and bottom ends. This is a raw rectangular material swatch, not a portrait or illustration.

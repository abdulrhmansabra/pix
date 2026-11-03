package com.example.pix.compose

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ContentScale
import androidx.compose.ui.graphics.Painter
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.drawLine
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/*
 * Coordinates and styling are taken from pix.css, not redesigned.
 * Source frame is 1080px wide; 3 source px = 1 design dp.
 * pix.svg is intentionally not approximated here. Supply the exact SVG
 * exports as Painter assets through PixArtwork (see COMPOSE_IMPLEMENTATION.md).
 */
private val Bg = Color(0xFF090A0B)
private val Surface = Color(0xFF1D1E22)
private val Card = Color(0xFF272A31)
private val TextPrimary = Color(0xFFF1F2F4)
private val TextMuted = Color(0xFF9DA1AD)
private val TextMutedDark = Color(0xFF686E7B)
private val Yellow = Color(0xFFF8CB4C)
private val Pink = Color(0xFFEE387D)
private val PremiumGradient = Brush.horizontalGradient(
    listOf(Color(0xFFFF9F51), Color(0xFFE23CA8), Color(0xFF6D4DE8))
)
private val HotGradient = Brush.horizontalGradient(
    listOf(Color(0xFFFF8A24), Color(0xFFFF3F65))
)

private fun px(value: Float) = (value / 3f).dp
private fun spx(value: Float) = (value / 3f).sp

/** Exact SVG artwork is injected; null means that source art is not yet mapped. */
data class PixArtwork(
    val search: Painter? = null,
    val gift: Painter? = null,
    val templateGift: Painter? = null,
    val profileGift: Painter? = null,
    val creditLightning: Painter? = null,
    val templateCreditLightning: Painter? = null,
    val profileCreditLightning: Painter? = null,
    val settings: Painter? = null,
    val agentCategory: Painter? = null,
    val discover: Painter? = null,
    val templates: Painter? = null,
    val inbox: Painter? = null,
    val profile: Painter? = null,
    val discoverActive: Painter? = null,
    val templatesActive: Painter? = null,
    val inboxActive: Painter? = null,
    val profileActive: Painter? = null,
    val usageSparkle: Painter? = null,
    val privateFolder: Painter? = null,
    val privateLock: Painter? = null,
    val collectionGrid: Painter? = null,
    val promotionGem: Painter? = null,
    val inviteGift: Painter? = null,
    val templatePhotos: List<Painter?> = emptyList(),
    val profilePhotos: List<Painter?> = emptyList()
)

data class PixTemplateItem(
    val title: String,
    val usageText: String = "",
    val photo: Painter? = null,
    val isHot: Boolean = false,
    val titleTopPx: Float = 0f
)

data class PixTemplateScreenText(
    val subscribe: String,
    val useTemplate: String,
    val hotBadge: String
)

data class PixProfileScreenText(
    val subscribe: String,
    val avatarInitial: String,
    val editProfile: String,
    val displayName: String,
    val handle: String,
    val followingCount: String,
    val followingLabel: String,
    val followersCount: String,
    val followersLabel: String,
    val subscriptionTitle: String,
    val subscriptionSubtitle: String,
    val inviteTitle: String,
    val inviteSubtitle: String,
    val videoFilter: String,
    val imageFilter: String,
    val agentFilter: String
)

/** Place a child in the 1080px Figma coordinate system. */
@Composable
private fun FixedLayer(
    x: Float,
    y: Float,
    width: Float,
    height: Float,
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit
) {
    Box(
        modifier = modifier
            .offset(x = px(x), y = px(y))
            .size(width = px(width), height = px(height)),
        content = content
    )
}

@Composable
private fun PixFrame(
    frameHeightPx: Float,
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit
) {
    val designHeight = px(frameHeightPx)
    BoxWithConstraints(modifier.fillMaxSize().background(Bg)) {
        val fitScale = minOf(maxWidth / 360.dp, maxHeight / designHeight)
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Box(
                Modifier
                    .requiredSize(360.dp, designHeight)
                    .clipToBounds()
                    .graphicsLayer {
                        scaleX = fitScale
                        scaleY = fitScale
                    },
                content = content
            )
        }
    }
}

@Composable
private fun SvgArt(painter: Painter?, modifier: Modifier = Modifier, scale: ContentScale = ContentScale.Fit) {
    if (painter != null) {
        Image(painter, contentDescription = null, modifier = modifier, contentScale = scale)
    }
}

@Composable
private fun PixText(
    value: String,
    fontPx: Float,
    color: Color = TextPrimary,
    weight: FontWeight = FontWeight.Normal,
    modifier: Modifier = Modifier,
    linePx: Float = fontPx * 1.2f,
    maxLines: Int = 1
) {
    Text(
        text = value,
        modifier = modifier,
        color = color,
        fontSize = spx(fontPx),
        lineHeight = spx(linePx),
        fontWeight = weight,
        maxLines = maxLines,
        overflow = TextOverflow.Clip
    )
}

@Composable
private fun PixGift(
    artwork: PixArtwork,
    x: Float,
    y: Float,
    width: Float,
    height: Float,
    onClick: (() -> Unit)? = null,
    artX: Float = 21.16f,
    artY: Float = 23.27f,
    artWidth: Float = 60.29f,
    artHeight: Float = 51.83f,
    icon: Painter? = artwork.gift
) {
    FixedLayer(x, y, width, height) {
        Box(
            Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(px(34.9f)))
                .background(Surface)
                .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
            contentAlignment = Alignment.TopStart
        ) {
            SvgArt(icon, Modifier.offset(px(artX), px(artY))
                .size(px(artWidth), px(artHeight)))
        }
    }
}

@Composable
private fun PixCreditPill(
    credits: String,
    subscribeLabel: String,
    artwork: PixArtwork,
    x: Float,
    y: Float,
    width: Float,
    height: Float,
    onSubscribe: (() -> Unit)?,
    lightningX: Float = 22.21f,
    lightningY: Float = 29.62f,
    lightningWidth: Float = 29.62f,
    lightningHeight: Float = 35.96f,
    creditX: Float = 64.53f,
    creditY: Float = 24.33f,
    creditFontPx: Float = 41.2537f,
    subscribeX: Float = 122.7f,
    subscribeY: Float = 11.64f,
    subscribeWidth: Float = 209.44f,
    subscribeHeight: Float = 74.05f,
    subscribeLabelX: Float = 21.16f,
    subscribeLabelY: Float = 17.98f,
    subscribeFontPx: Float = 37.0225f,
    lightningPainter: Painter? = artwork.creditLightning
) {
    FixedLayer(x, y, width, height) {
        Box(
            Modifier.fillMaxSize()
                .clip(RoundedCornerShape(px(49.7f)))
                .background(Surface)
        )
        SvgArt(
            lightningPainter,
            Modifier.offset(px(lightningX), px(lightningY))
                .size(px(lightningWidth), px(lightningHeight))
        )
        PixText(
            credits, creditFontPx, Yellow,
            modifier = Modifier.offset(px(creditX), px(creditY)).width(px(47f)).height(px(48f)),
            linePx = 48f
        )
        Box(
            Modifier.offset(px(subscribeX), px(subscribeY))
                .size(px(subscribeWidth), px(subscribeHeight))
                .clip(RoundedCornerShape(px(38.95f)))
                .background(PremiumGradient)
                .then(if (onSubscribe != null) Modifier.clickable { onSubscribe() } else Modifier),
            contentAlignment = Alignment.TopStart
        ) {
            PixText(
                subscribeLabel, subscribeFontPx, TextPrimary, FontWeight.Medium,
                modifier = Modifier.offset(px(subscribeLabelX), px(subscribeLabelY))
                    .width(px(166f)).height(px(43f)),
                linePx = 43f
            )
        }
    }
}

@Composable
private fun PixPlus() {
    Canvas(Modifier.size(px(35.79f))) {
        val width = size.minDimension * 0.17f
        drawLine(Color.White, Offset(size.width / 2f, 0f),
            Offset(size.width / 2f, size.height), width, cap = StrokeCap.Square)
        drawLine(Color.White, Offset(0f, size.height / 2f),
            Offset(size.width, size.height / 2f), width, cap = StrokeCap.Square)
    }
}

@Composable
private fun PixBottomNav(
    top: Float,
    height: Float,
    artwork: PixArtwork,
    selected: String,
    onDiscover: (() -> Unit)?,
    onTemplates: (() -> Unit)?,
    onInbox: (() -> Unit)?,
    onProfile: (() -> Unit)?,
    onCreate: (() -> Unit)?
) {
    val discoverIcon = if (selected == "Discover") artwork.discoverActive ?: artwork.discover else artwork.discover
    val templatesIcon = if (selected == "Template") artwork.templatesActive ?: artwork.templates else artwork.templates
    val inboxIcon = if (selected == "Inbox") artwork.inboxActive ?: artwork.inbox else artwork.inbox
    val profileIcon = if (selected == "Mine") artwork.profileActive ?: artwork.profile else artwork.profile
    FixedLayer(0f, top, 1080f, height) {
        Box(Modifier.fillMaxSize().background(Bg))
        PixBottomItem("Discover", discoverIcon, 28.42f, onDiscover)
        PixBottomItem("Template", templatesIcon, 244.21f, onTemplates)
        PixBottomItem("Inbox", inboxIcon, 676.84f, onInbox)
        PixBottomItem("Mine", profileIcon, 892.63f, onProfile)
        FixedLayer(483.16f, 27.37f, 113.68f, 113.68f) {
            Box(
                Modifier.fillMaxSize().clip(CircleShape).background(PremiumGradient)
                    .then(if (onCreate != null) Modifier.clickable { onCreate() } else Modifier),
                contentAlignment = Alignment.Center
            ) { PixPlus() }
        }
    }
}

@Composable
private fun BoxScope.PixBottomItem(
    label: String,
    painter: Painter?,
    x: Float,
    onClick: (() -> Unit)?
) {
    FixedLayer(x, 31.58f, 157.89f, 111.84f) {
        Column(
            Modifier.fillMaxSize()
                .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(px(12.63f), Alignment.CenterVertically)
        ) {
            SvgArt(painter, Modifier.size(px(64.21f)))
            PixText(label, 29.47f, linePx = 35f)
        }
    }
}

@Composable
private fun PixCategory(label: String, widthPx: Float, selected: Boolean, agentIcon: Painter? = null) {
    val borderColor = if (selected) Color(0xFFEDEEF1) else Color(0xFF686F7E)
    val textColor = when {
        selected -> TextPrimary
        label == "Agent" -> Color(0xFF9941AA)
        else -> TextMuted
    }
    Box(
        Modifier.width(px(widthPx)).height(px(104.72f))
            .clip(RoundedCornerShape(px(27.5f)))
            .border(px(2.85f), borderColor, RoundedCornerShape(px(27.5f))),
        contentAlignment = Alignment.Center
    ) {
        if (label == "Agent" && agentIcon != null) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(px(10f)),
                verticalAlignment = Alignment.CenterVertically
            ) {
                SvgArt(agentIcon, Modifier.size(px(35.96f)))
                PixText(label, 35.96f, textColor, FontWeight.Medium, linePx = 42f)
            }
        } else {
            PixText(label, 35.96f, textColor, FontWeight.Medium, linePx = 42f)
        }
    }
}

@Composable
private fun PixTemplateCard(
    item: PixTemplateItem,
    photo: Painter?,
    x: Float,
    y: Float,
    useTemplateLabel: String,
    hotLabel: String,
    usageIcon: Painter?,
    onClick: (() -> Unit)?
) {
    FixedLayer(x, y, 523.6f, 804.98f) {
        Box(
            Modifier.fillMaxSize()
                .clip(RoundedCornerShape(px(44.43f)))
                .background(Card)
        ) {
            SvgArt(
                photo,
                Modifier.size(px(523.6f), px(698.14f))
                    .clip(RoundedCornerShape(topStart = px(44.43f), topEnd = px(44.43f))),
                ContentScale.Crop
            )
            if (item.isHot) {
                Box(
                    Modifier.offset(px(17.98f), px(17.98f))
                        .size(px(86.74f), px(49.72f))
                        .clip(RoundedCornerShape(px(13.75f)))
                        .background(HotGradient),
                    contentAlignment = Alignment.Center
                ) {
                    PixText(hotLabel, 23.27f, Color.White, FontWeight.Bold, linePx = 27f)
                }
            }
            Box(
                Modifier.offset(px(16.92f), px(581.78f))
                    .size(px(489.76f), px(105.78f))
            ) {
                PixText(
                    item.title, 35.96f,
                    modifier = Modifier.offset(y = px(item.titleTopPx))
                        .width(px(375.51f)).height(px(100f)),
                    weight = FontWeight.Medium, linePx = 50f, maxLines = 2
                )
                if (item.usageText.isNotEmpty()) {
                    SvgArt(usageIcon, Modifier.offset(px(0f), px(6.35f))
                        .size(px(25.39f)))
                    PixText(
                        item.usageText, 35.96f,
                        modifier = Modifier.offset(px(34.91f), 0.dp)
                            .width(px(93f)).height(px(42f)),
                        linePx = 42f
                    )
                }
            }
            Box(
                Modifier.offset(y = px(698.14f)).fillMaxWidth().height(px(106.84f))
                    .background(Card)
                    .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
                contentAlignment = Alignment.Center
            ) {
                PixText(useTemplateLabel, 38.08f, TextPrimary, FontWeight.Medium, linePx = 45f)
            }
        }
    }
}

/**
 * Template browsing frame (1080 x 2115 px).
 * Text and artwork values are explicit inputs so SVG text outlines and images
 * are never replaced with guessed content.
 */
@Composable
fun PixTemplateBrowsingScreen(
    text: PixTemplateScreenText,
    credits: String,
    templates: List<PixTemplateItem>,
    artwork: PixArtwork = PixArtwork(),
    modifier: Modifier = Modifier,
    onSearch: (() -> Unit)? = null,
    onGift: (() -> Unit)? = null,
    onSubscribe: (() -> Unit)? = null,
    onTemplateClick: ((PixTemplateItem) -> Unit)? = null,
    onDiscover: (() -> Unit)? = null,
    onTemplates: (() -> Unit)? = null,
    onInbox: (() -> Unit)? = null,
    onProfile: (() -> Unit)? = null,
    onCreate: (() -> Unit)? = null
) {
    PixFrame(2115f, modifier) {
        // Top navigation / Search
        SvgArt(
            artwork.search,
            Modifier.offset(px(42.31f), px(50.77f)).size(px(63.47f))
                .then(if (onSearch != null) Modifier.clickable { onSearch() } else Modifier)
        )
        PixGift(artwork, 570.15f, 30.68f, 102.61f, 96.26f, onGift,
            icon = artwork.templateGift ?: artwork.gift)
        PixCreditPill(
            credits, text.subscribe, artwork, 700.25f, 30.68f, 344.84f, 96.26f, onSubscribe,
            lightningPainter = artwork.templateCreditLightning ?: artwork.creditLightning
        )

        // Scrollable template categories
        Row(
            Modifier.offset(px(16.92f), px(204.15f))
                .width(px(1093.75f)).height(px(107.89f))
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(px(17.98f))
        ) {
            PixCategory("Favorite", 200.98f, false)
            PixCategory("Trend", 163.96f, true)
            PixCategory("Casual", 181.94f, false)
            PixCategory("Night Mood", 257.04f, false)
            PixCategory("Agent", 217.9f, false, artwork.agentCategory)
        }

        // Template cards: the four positions and dimensions come directly from pix.css.
        val cardPositions = listOf(
            10.58f to 350.13f,
            545.82f to 350.13f,
            10.58f to 1165.68f,
            545.82f to 1165.68f
        )
        cardPositions.forEachIndexed { index, pos ->
            templates.getOrNull(index)?.let { item ->
                val photo = item.photo ?: artwork.templatePhotos.getOrNull(index)
                PixTemplateCard(
                    item, photo, pos.first, pos.second, text.useTemplate, text.hotBadge,
                    artwork.usageSparkle,
                    onTemplateClick?.let { callback -> { callback(item) } }
                )
            }
        }

        PixBottomNav(
            1938.92f, 172.42f, artwork, "Template",
            onDiscover, onTemplates, onInbox, onProfile, onCreate
        )
    }
}

@Composable
private fun PixProfilePromotion(
    title: String,
    subtitle: String,
    x: Float,
    y: Float,
    gradient: Brush,
    artwork: Painter?,
    titleBrush: Brush? = null
) {
    FixedLayer(x, y, 517.89f, 180f) {
        Box(
            Modifier.fillMaxSize()
                .clip(RoundedCornerShape(px(46.32f)))
                .background(gradient)
        ) {
            Text(
                title,
                Modifier.offset(px(32.63f), px(45.26f)),
                color = Color.White,
                fontSize = spx(48.42f),
                lineHeight = spx(57f),
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Clip,
                style = if (titleBrush != null) androidx.compose.ui.text.TextStyle(brush = titleBrush)
                       else androidx.compose.ui.text.TextStyle.Default
            )
            PixText(
                subtitle, 29.47f, Color(0xFFF4C4DA),
                modifier = Modifier.offset(px(32.63f), px(105.26f)), linePx = 35f
            )
            SvgArt(artwork, Modifier.offset(px(385.26f), px(42.11f))
                .size(px(98.95f), px(102.11f)))
        }
    }
}

@Composable
private fun PixProfileInvite(
    title: String,
    subtitle: String,
    x: Float,
    y: Float,
    artwork: Painter?
) {
    FixedLayer(x, y, 516.84f, 180f) {
        Box(
            Modifier.fillMaxSize()
                .clip(RoundedCornerShape(px(46.32f)))
                .background(Brush.horizontalGradient(listOf(Color(0xFF3A2719), Color(0xFF35172D))))
        ) {
            Text(
                title,
                Modifier.offset(px(32.63f), px(45.26f)),
                fontSize = spx(48.42f),
                lineHeight = spx(57f),
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Clip,
                style = androidx.compose.ui.text.TextStyle(
                    brush = Brush.horizontalGradient(listOf(Color(0xFFFF995F), Color(0xFFDF43A8)))
                )
            )
            PixText(
                subtitle, 29.47f, Color(0xFFB4A8A8),
                modifier = Modifier.offset(px(32.63f), px(105.26f)), linePx = 35f
            )
            SvgArt(artwork, Modifier.offset(px(385.26f), px(47.37f))
                .size(px(92.63f), px(84.21f)))
        }
    }
}

/**
 * Profile frame (1080 x 2106 px). SVG artwork is injected from exported,
 * named SVG groups; text remains caller-supplied to preserve the original.
 */
@Composable
fun PixProfileScreen(
    text: PixProfileScreenText,
    credits: String,
    artwork: PixArtwork = PixArtwork(),
    modifier: Modifier = Modifier,
    onSettings: (() -> Unit)? = null,
    onGift: (() -> Unit)? = null,
    onSubscribe: (() -> Unit)? = null,
    onEditProfile: (() -> Unit)? = null,
    onPrivateTab: (() -> Unit)? = null,
    onCollectionTab: (() -> Unit)? = null,
    onVideoFilter: (() -> Unit)? = null,
    onImageFilter: (() -> Unit)? = null,
    onAgentFilter: (() -> Unit)? = null,
    onDiscover: (() -> Unit)? = null,
    onTemplates: (() -> Unit)? = null,
    onInbox: (() -> Unit)? = null,
    onProfile: (() -> Unit)? = null,
    onCreate: (() -> Unit)? = null
) {
    PixFrame(2106f, modifier) {
        // Subtle profile header glow
        Canvas(Modifier.fillMaxWidth().height(px(589.47f))) {
            drawRect(
                Brush.radialGradient(
                    colors = listOf(Color(0xB82B1426), Color.Transparent),
                    center = Offset(size.width * 0.7636f, 0f),
                    radius = size.width * 0.9091f
                )
            )
        }

        // Top navigation / Profile
        SvgArt(
            artwork.settings,
            Modifier.offset(px(42.11f), px(50.53f)).size(px(63.16f))
                .then(if (onSettings != null) Modifier.clickable { onSettings() } else Modifier)
        )
        PixGift(
            artwork, 570.53f, 30.53f, 102.11f, 95.79f, onGift,
            artX = 21.05f, artY = 23.16f, artWidth = 60f, artHeight = 51.58f,
            icon = artwork.profileGift ?: artwork.gift
        )
        PixCreditPill(
            credits, text.subscribe, artwork, 700f, 30.53f, 343.16f, 95.79f, onSubscribe,
            lightningX = 22.11f, lightningY = 29.47f,
            lightningWidth = 29.47f, lightningHeight = 35.79f,
            creditX = 64.21f, creditY = 24.21f, creditFontPx = 41.0526f,
            subscribeX = 122.11f, subscribeY = 11.58f,
            subscribeWidth = 208.42f, subscribeHeight = 73.68f,
            subscribeLabelX = 21.05f, subscribeLabelY = 17.89f,
            subscribeFontPx = 36.8421f,
            lightningPainter = artwork.profileCreditLightning ?: artwork.creditLightning
        )

        // Profile avatar and initial
        FixedLayer(43.16f, 181.05f, 200f, 200f) {
            Box(
                Modifier.fillMaxSize().clip(CircleShape).background(Pink)
                    .border(px(3.16f), Color(0xFF303338), CircleShape),
                contentAlignment = Alignment.TopStart
            ) {
                PixText(
                    text.avatarInitial, 105.26f, Color.White,
                    modifier = Modifier.offset(px(62.11f), px(44.21f))
                        .width(px(69f)).height(px(123f)),
                    linePx = 123f
                )
            }
        }

        // Edit profile button
        FixedLayer(791.58f, 235.79f, 266.32f, 90.53f) {
            Box(
                Modifier.fillMaxSize().clip(RoundedCornerShape(px(33.68f)))
                    .background(Color(0xFF302A36))
                    .then(if (onEditProfile != null) Modifier.clickable { onEditProfile() } else Modifier),
                contentAlignment = Alignment.TopStart
            ) {
                PixText(
                    text.editProfile, 35.79f, Color(0xFFDAD8DF), FontWeight.Medium,
                    modifier = Modifier.offset(px(44.21f), px(26.32f))
                        .width(px(175f)).height(px(42f)),
                    linePx = 42f
                )
            }
        }

        PixText(text.displayName, 71.05f, modifier = Modifier.offset(px(42.11f), px(412.63f)),
            weight = FontWeight.Medium, linePx = 83f)
        PixText(text.handle, 40f, TextMutedDark, modifier = Modifier.offset(px(43.16f), px(503.16f)),
            linePx = 47f)

        // Profile statistics
        FixedLayer(43.16f, 613.68f, 463.16f, 55.79f) {
            PixText(text.followingCount, 37.89f,
                modifier = Modifier.width(px(22f)).height(px(44f)), linePx = 44f)
            PixText(text.followingLabel, 37.89f, TextMutedDark,
                modifier = Modifier.offset(px(32.53f), 0.dp)
                    .width(px(163f)).height(px(44f)), linePx = 44f)
            PixText(text.followersCount, 37.89f,
                modifier = Modifier.offset(px(241.05f), 0.dp)
                    .width(px(22f)).height(px(44f)), linePx = 44f)
            PixText(text.followersLabel, 37.89f, TextMutedDark,
                modifier = Modifier.offset(px(273.58f), 0.dp)
                    .width(px(164f)).height(px(44f)), linePx = 44f)
        }

        // Promotion cards
        PixProfilePromotion(
            text.subscriptionTitle, text.subscriptionSubtitle, 16.84f, 716.84f,
            PremiumGradient, artwork.promotionGem
        )
        PixProfileInvite(
            text.inviteTitle, text.inviteSubtitle, 546.31f, 716.84f, artwork.inviteGift
        )

        // Content navigation and tabs
        FixedLayer(0f, 920f, 1080f, 109.47f) {
            Box(Modifier.fillMaxSize())
            FixedLayer(0f, 0f, 540f, 109.47f) {
                SvgArt(artwork.privateFolder, Modifier.offset(px(243.16f), px(16.84f))
                    .size(px(50.53f), px(48.42f)))
                SvgArt(artwork.privateLock, Modifier.offset(px(278.95f), px(46.32f))
                    .size(px(16.84f), px(18.95f)))
                Box(Modifier.align(Alignment.BottomStart).fillMaxWidth().height(px(3.16f))
                    .background(Color(0xFFD8DADD)))
                if (onPrivateTab != null) Box(Modifier.fillMaxSize().clickable { onPrivateTab() })
            }
            FixedLayer(540f, 0f, 540f, 109.47f) {
                SvgArt(artwork.collectionGrid, Modifier.offset(px(246.32f), px(17.89f))
                    .size(px(47.37f), px(46.32f)))
                Box(Modifier.align(Alignment.BottomStart).fillMaxWidth().height(px(3.16f))
                    .background(Color(0xFF25282D)))
                if (onCollectionTab != null) Box(Modifier.fillMaxSize().clickable { onCollectionTab() })
            }
        }

        // Media type filters
        Row(
            Modifier.offset(px(16.84f), px(1060f))
                .width(px(541.05f)).height(px(98.95f)),
            horizontalArrangement = Arrangement.spacedBy(px(17.89f))
        ) {
            PixFilter(text.videoFilter, 163.16f, true, onVideoFilter)
            PixFilter(text.imageFilter, 171.58f, false, onImageFilter)
            PixFilter(text.agentFilter, 170.53f, false, onAgentFilter)
        }

        // Original photos are injected as photo slots; empty slots remain empty.
        val thumbPositions = listOf(0f to 1193.68f, 363.16f to 1193.68f)
        thumbPositions.forEachIndexed { index, pos ->
            artwork.profilePhotos.getOrNull(index)?.let { painter ->
                FixedLayer(pos.first, pos.second, 353.68f, 441.05f) {
                    SvgArt(painter, Modifier.fillMaxSize(), ContentScale.Crop)
                }
            }
        }

        PixBottomNav(
            1933.68f, 171.58f, artwork, "Mine",
            onDiscover, onTemplates, onInbox, onProfile, onCreate
        )
    }
}

@Composable
private fun PixFilter(label: String, width: Float, selected: Boolean, onClick: (() -> Unit)?) {
    val stroke = if (selected) Color(0xFFE5E6E9) else Color(0xFF999EAB)
    val text = if (selected) TextPrimary else TextMuted
    Box(
        Modifier.width(px(width)).height(px(97.89f))
            .clip(RoundedCornerShape(px(28.42f)))
            .border(px(2.84f), stroke, RoundedCornerShape(px(28.42f)))
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
        contentAlignment = Alignment.Center
    ) {
        PixText(label, 35.79f, text, FontWeight.Medium, linePx = 42f)
    }
}

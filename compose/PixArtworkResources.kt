package com.example.pix.compose

import androidx.compose.runtime.Composable
import androidx.compose.ui.res.painterResource
import com.example.pix.R

/**
 * Loads the exact artwork exported from pix.svg into PixArtwork.
 *
 * Keep the matching WebP files in app/src/main/res/drawable-nodpi.
 * If the app uses a different Android namespace, change only the R import.
 */
@Composable
fun rememberPixArtwork(): PixArtwork = PixArtwork(
    search = painterResource(R.drawable.pix_search),
    gift = painterResource(R.drawable.pix_profile_gift_action),
    templateGift = painterResource(R.drawable.pix_template_gift_action),
    profileGift = painterResource(R.drawable.pix_profile_gift_action),
    creditLightning = painterResource(R.drawable.pix_credit_lightning_template),
    templateCreditLightning = painterResource(R.drawable.pix_credit_lightning_template),
    profileCreditLightning = painterResource(R.drawable.pix_credit_lightning_profile),
    settings = painterResource(R.drawable.pix_settings),
    agentCategory = painterResource(R.drawable.pix_agent_category),
    discover = painterResource(R.drawable.pix_nav_discover),
    templates = painterResource(R.drawable.pix_nav_templates),
    inbox = painterResource(R.drawable.pix_nav_inbox),
    profile = painterResource(R.drawable.pix_nav_profile),
    templatesActive = painterResource(R.drawable.pix_nav_templates_active),
    profileActive = painterResource(R.drawable.pix_nav_profile_active),
    usageSparkle = painterResource(R.drawable.pix_usage_sparkle),
    privateFolder = painterResource(R.drawable.pix_private_folder),
    privateLock = painterResource(R.drawable.pix_private_lock),
    collectionGrid = painterResource(R.drawable.pix_collection_grid),
    promotionGem = painterResource(R.drawable.pix_promotion_gem),
    inviteGift = painterResource(R.drawable.pix_invite_gift),
    templatePhotos = listOf(
        painterResource(R.drawable.pix_template_photo_01),
        painterResource(R.drawable.pix_template_photo_02),
        painterResource(R.drawable.pix_template_photo_03),
        painterResource(R.drawable.pix_template_photo_04)
    ),
    profilePhotos = listOf(
        painterResource(R.drawable.pix_profile_photo_01),
        painterResource(R.drawable.pix_profile_photo_02)
    )
)

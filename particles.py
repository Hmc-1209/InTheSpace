import pygame
from GlobalVariables import screen_width


# ------------------------ Particles ------------------------
def circle_surf(radius, color):
    surf = pygame.Surface((radius * 2, radius * 2))
    pygame.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf


def particles(screen, particle1_group, screen_scroll):
    for particle in particle1_group:
        particle[0][0] += particle[1][0] + screen_scroll
        particle[0][1] += particle[1][1]
        particle[2] -= 0.1
        particle[1][1] += 0.2
        particle[3] += screen_scroll

        if not (particle[0][0] < 0 or particle[0][0] > screen_width()):
            pygame.draw.circle(screen, particle[5], [int(particle[0][0]), int(particle[0][1])], int(particle[2]))

        radius = particle[2] * 2
        screen.blit(circle_surf(radius, particle[4]), (int(particle[0][0] - radius), int(particle[0][1] - radius)),
                    special_flags=pygame.BLEND_RGB_ADD)
        if particle[2] <= 0 or particle[0][0] < 0 or particle[0][0] > screen_width():
            particle1_group.remove(particle)
